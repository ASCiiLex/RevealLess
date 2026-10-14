import logging
import os

logger = logging.getLogger(__name__)

CONFIANZA_MINIMA = 0.6
# Modelo base de todos los servicios de IA; ANTHROPIC_MODEL solo cambia el de la frontera.
MODELO_IA = 'claude-haiku-4-5-20251001'
TIMEOUT_PUBLICAR = 8
# El autor espera con el botón pulsado: margen para un modelo mayor.
TIMEOUT_SUGERENCIA = 20
MAX_REVELACIONES = 6

SYSTEM_PROMPT = (
    'Eres el asistente antispoiler de RevealLess. Recibes el texto de una publicación sobre una obra '
    'y la lista de sus unidades narrativas (arcos, episodios, capítulos) ordenadas por posición de consumo.\n'
    '1. parte_id: la unidad donde ocurre la escena o el momento que comenta el texto. '
    'Si el autor ya la ha indicado, usa esa.\n'
    '2. revelaciones: cada hecho de la trama que el texto revela o da por sabido y que alguien que solo '
    'haya llegado a esa parte todavía no conoce (identidades ocultas, muertes, transformaciones, giros, '
    'relaciones). Para cada hecho, la unidad donde la obra lo confirma por primera vez: si se insinúa antes '
    'y se confirma después, la confirmación. Prefiere un episodio o capítulo concreto; si no sabes cuál, '
    'el arco donde ocurre. Lo que ya se sabe en esa parte no es una revelación. Si no hay ninguna, deja la lista vacía.\n'
    '3. confianza: de 0 a 1, por cada revelación y una general (la parte es correcta y no falta ninguna revelación).\n'
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
        return self.frontera_spoiler is not None and self.confianza >= CONFIANZA_MINIMA


def etiqueta_unidad(unidad):
    return f'{unidad.padre.nombre} · {unidad.nombre}' if unidad.padre_id else unidad.nombre


def proponer_clasificacion(texto, obra, referencia=None, timeout=TIMEOUT_PUBLICAR):
    """Punto único de entrada a la IA de clasificación. Nunca lanza: cualquier fallo devuelve una
    sugerencia no utilizable y quien llama cae al fallback sin bloquear la publicación."""
    try:
        return _llamar_api(texto, obra, referencia, timeout)
    except Exception:
        logger.exception('Fallo al llamar a la API de IA de clasificación')
        return SugerenciaIA()


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

    client = anthropic.Anthropic(api_key=api_key, timeout=timeout)
    response = client.messages.create(
        model=os.environ.get('ANTHROPIC_MODEL') or MODELO_IA,
        max_tokens=800,
        system=SYSTEM_PROMPT,
        tools=[HERRAMIENTA],
        tool_choice={'type': 'tool', 'name': HERRAMIENTA['name']},
        messages=[{'role': 'user', 'content': user_prompt}],
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
    Un id inventado invalida toda la propuesta: podría ser justo la revelación más tardía."""
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