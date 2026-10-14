import logging
import os

logger = logging.getLogger(__name__)

CONFIANZA_MINIMA = 0.6
# Modelo base de todos los servicios de IA; ANTHROPIC_MODEL solo cambia el de la frontera.
MODELO_IA = 'claude-haiku-4-5-20251001'
# Generación 4: admite forzar la herramienta y fijar temperature. Las 5.x lo rechazan con 400.
PREFIJOS_CON_FORZADO = ('claude-haiku-4', 'claude-sonnet-4', 'claude-opus-4')
TIMEOUT_PUBLICAR = 8
# El autor espera con el botón pulsado: margen para un modelo que razona antes de responder.
TIMEOUT_SUGERENCIA = 45
MAX_REVELACIONES = 6

SYSTEM_PROMPT = (
    'Eres el asistente antispoiler de RevealLess. Recibes el texto de una publicación sobre una obra '
    'y la lista de sus unidades narrativas (arcos, episodios, capítulos) ordenadas por posición de consumo. '
    'Responde siempre llamando a la herramienta clasificar_frontera.\n'
    '1. parte_id: la unidad donde ocurre la escena o el momento que comenta el texto. '
    'Si el autor ya la ha indicado, usa esa.\n'
    '2. revelaciones: cada hecho de la trama que el texto revela o da por sabido y que alguien que solo '
    'haya llegado a esa parte todavía no conoce (identidades ocultas, muertes, transformaciones, giros, '
    'relaciones). Solo hechos que estén en el texto: no añadas nada que el texto no diga. Para cada hecho, '
    'la unidad donde la obra lo confirma por primera vez: si se insinúa antes y se confirma después, la '
    'confirmación. Prefiere un episodio o capítulo concreto; si no sabes cuál, el arco donde ocurre. '
    'Lo que ya se sabe en esa parte no es una revelación. Si no hay ninguna, deja la lista vacía.\n'
    '3. confianza: de 0 a 1, por cada revelación y una general (la parte es correcta y no falta ninguna '
    'revelación). Si no sabes dónde se confirma un hecho, no elijas el final de la obra para cubrirte: '
    'elige tu mejor estimación y da una confianza baja.\n'
    'No calcules la frontera: será la revelación más tardía. Usa solo ids de la lista.'
)

HERRAMIENTA = {
    'name': 'clasificar_frontera',
    'description': 'Registra la parte que comenta el texto y los hechos que revela, cada uno con la unidad donde la obra lo confirma.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'parte_id': {'type': 'integer', 'description': 'id de la unidad donde ocurre lo que comenta el texto'},
            'revelaciones': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'hecho': {'type': 'string', 'description': 'hecho revelado, en una frase corta'},
                        'unidad_id': {'type': 'integer', 'description': 'id de la unidad donde se confirma'},
                        'confianza': {'type': 'number'},
                    },
                    'required': ['hecho', 'unidad_id', 'confianza'],
                },
            },
            'confianza': {'type': 'number', 'description': 'confianza general, entre 0 y 1'},
        },
        'required': ['parte_id', 'revelaciones', 'confianza'],
    },
}


class Revelacion:
    # El hecho solo obliga al modelo a razonar; nunca sale del servidor (sería un spoiler para el autor).
    def __init__(self, hecho, unidad, confianza):
        self.hecho = hecho
        self.unidad = unidad
        self.confianza = confianza


class SugerenciaIA:
    def __init__(self, frontera_spoiler=None, confianza=0.0, parte=None, revelaciones=()):
        self.frontera_spoiler = frontera_spoiler
        self.confianza = confianza
        self.parte = parte
        self.revelaciones = list(revelaciones)

    @property
    def es_utilizable(self):
        """Umbral para decidir sin revisión humana (al publicar). En la sugerencia revisa el autor."""
        return self.frontera_spoiler is not None and self.confianza >= CONFIANZA_MINIMA


def etiqueta_unidad(unidad):
    return f'{unidad.padre.nombre} · {unidad.nombre}' if unidad.padre_id else unidad.nombre


def proponer_clasificacion(texto, obra, referencia=None, timeout=TIMEOUT_PUBLICAR):
    """Punto único de entrada a la IA de clasificación. Nunca lanza: cualquier fallo devuelve una
    sugerencia vacía y quien llama cae al fallback sin bloquear la publicación."""
    try:
        return _llamar_api(texto, obra, referencia, timeout)
    except Exception:
        logger.exception('Fallo al llamar a la API de IA de clasificación')
        return SugerenciaIA()


def _parametros_modelo(modelo):
    """Forzado y determinista donde se admite. En 5.x la herramienta se pide en el prompt, con margen
    de tokens para el razonamiento y esfuerzo bajo para acotar la espera."""
    if modelo.startswith(PREFIJOS_CON_FORZADO):
        return {
            'max_tokens': 800,
            'temperature': 0,
            'tool_choice': {'type': 'tool', 'name': HERRAMIENTA['name']},
        }
    return {
        'max_tokens': 8000,
        'tool_choice': {'type': 'auto'},
        # extra_body: válido con cualquier versión del SDK, aunque no declare output_config.
        'extra_body': {'output_config': {'effort': 'low'}},
    }


def _candidatas(unidades):
    """Descarta las unidades que abarcan la obra entera: como parte o revelación llevarían la frontera al final."""
    inicio = min(u.orden_inicio for u in unidades)
    fin = max(u.orden_fin for u in unidades)
    utiles = [u for u in unidades if not (u.orden_inicio <= inicio and u.orden_fin >= fin)]
    return utiles or unidades


def _llamar_api(texto, obra, referencia, timeout):
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise RuntimeError('ANTHROPIC_API_KEY no configurada.')

    import anthropic
    from .models import UnidadNarrativa

    unidades = list(
        UnidadNarrativa.objects.filter(obra=obra).select_related('padre').order_by('orden_inicio')
    )
    if not unidades:
        raise RuntimeError('La obra no tiene unidades narrativas.')
    unidades = _candidatas(unidades)

    lineas = '\n'.join(
        f'{u.id} | {u.tipo} | {etiqueta_unidad(u)} | {u.orden_inicio}-{u.orden_fin}' for u in unidades
    )
    parte = (
        f'Parte indicada por el autor: id={referencia.id} ({etiqueta_unidad(referencia)}).'
        if referencia else 'El autor no ha indicado la parte: proponla en parte_id.'
    )
    user_prompt = (
        f'Obra: {obra.titulo}\n{parte}\n\n'
        f'Unidades (id | tipo | nombre | orden):\n{lineas}\n\n'
        f'Texto de la publicación:\n"""{texto}"""'
    )

    modelo = os.environ.get('ANTHROPIC_MODEL') or MODELO_IA
    client = anthropic.Anthropic(api_key=api_key, timeout=timeout)
    response = client.messages.create(
        model=modelo,
        system=SYSTEM_PROMPT,
        tools=[HERRAMIENTA],
        messages=[{'role': 'user', 'content': user_prompt}],
        **_parametros_modelo(modelo),
    )

    bloque = next((b for b in response.content if b.type == 'tool_use'), None)
    if bloque is None:
        raise RuntimeError('La respuesta de la IA no incluyó una clasificación.')

    return _resolver(bloque.input, {u.id: u for u in unidades}, referencia)


def _entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _acotar(valor):
    try:
        return max(0.0, min(1.0, float(valor)))
    except (TypeError, ValueError):
        return 0.0


def _unidad(unidades_por_id, valor):
    unidad = unidades_por_id.get(_entero(valor))
    if unidad is None:
        raise RuntimeError(f'La IA propuso un id inexistente: {valor}')
    return unidad


def _resolver(entrada, unidades_por_id, referencia):
    """Frontera = la revelación más tardía, nunca anterior a la parte. Confianza = la mínima.
    Un id inventado o excluido invalida toda la propuesta: podría ser justo la revelación más tardía."""
    parte = referencia or _unidad(unidades_por_id, entrada.get('parte_id'))
    revelaciones = []
    for r in (entrada.get('revelaciones') or [])[:MAX_REVELACIONES]:
        hecho = ' '.join(str(r.get('hecho') or '').split())[:200]
        if hecho:
            revelaciones.append(
                Revelacion(hecho, _unidad(unidades_por_id, r.get('unidad_id')), _acotar(r.get('confianza')))
            )
    revelaciones.sort(key=lambda r: r.unidad.orden_fin)

    confianza = min([_acotar(entrada.get('confianza'))] + [r.confianza for r in revelaciones])
    frontera = max([parte] + [r.unidad for r in revelaciones], key=lambda u: u.orden_fin)
    return SugerenciaIA(frontera, confianza, parte, revelaciones)