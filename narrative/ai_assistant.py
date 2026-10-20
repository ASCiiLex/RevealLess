import logging
import re

from django.conf import settings

from ia.cliente import llamar_claude
from ia.models import UsoIA

logger = logging.getLogger(__name__)

CONFIANZA_MINIMA = 0.6
# Tope cuando la IA elige una unidad sin título: no puede saber qué ocurre en ella. Por debajo del umbral.
CONFIANZA_MAX_SIN_NOMBRE = 0.5
# «Episodio 227», «Capítulo 12», «Vol. 3»...: unidades sin título propio.
NOMBRE_GENERICO = re.compile(
    r'^(episodio|episode|ep\.?|cap[ií]tulo|chapter|cap\.?|volumen|vol\.?|tomo)\s*\d+$', re.IGNORECASE
)
# Modelo de los servicios de catálogo (traducción, personajes). Las fronteras usan IA_MODELO_FRONTERAS.
MODELO_IA = 'claude-haiku-4-5-20251001'
# Generación 4: admite forzar la herramienta y fijar temperature. Las 5.x lo rechazan con 400.
PREFIJOS_CON_FORZADO = ('claude-haiku-4', 'claude-sonnet-4', 'claude-opus-4')
# Si se agota, se publica con el fallback seguro (progreso del autor).
TIMEOUT_PUBLICAR = 12
# El autor espera con el botón pulsado: margen para un modelo que razona antes de responder.
TIMEOUT_SUGERENCIA = 45
MAX_REVELACIONES = 6

SYSTEM_PROMPT = (
    'Eres el asistente antispoiler de RevealLess. Recibes el texto de una publicación sobre una obra '
    'y la lista de sus unidades narrativas (arcos, episodios, capítulos) ordenadas por posición de consumo. '
    'Las unidades son de una versión concreta (libro, serie, película, manga...): sitúa cada hecho según '
    'esa versión, no según otras adaptaciones de la misma historia, que a veces lo cuentan en otro momento. '
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


class RespuestaInvalida(RuntimeError):
    """La IA respondió con un formato o unos ids que no se pueden usar: se descarta entera."""


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


def modelo_fronteras():
    return getattr(settings, 'IA_MODELO_FRONTERAS', MODELO_IA)


def etiqueta_unidad(unidad):
    return f'{unidad.padre.nombre} · {unidad.nombre}' if unidad.padre_id else unidad.nombre


def es_nombre_generico(unidad):
    return bool(NOMBRE_GENERICO.match(unidad.nombre.strip()))


def proponer_clasificacion(
    texto, obra, referencia=None, timeout=TIMEOUT_PUBLICAR, usuario=None,
    funcion=UsoIA.FUNCION_CLASIFICACION, modelo=None,
):
    """Punto único de entrada a la IA de clasificación. Nunca lanza: cualquier fallo devuelve una
    sugerencia vacía y quien llama cae al fallback sin bloquear la publicación.
    usuario y funcion: registro de uso. modelo: solo para evaluar; por defecto IA_MODELO_FRONTERAS."""
    try:
        return _llamar_api(texto, obra, referencia, timeout, usuario, funcion, modelo)
    except RespuestaInvalida as e:
        logger.warning('Propuesta de la IA descartada: %s', e)
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


def _llamar_api(texto, obra, referencia, timeout, usuario, funcion, modelo):
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
    contexto_obra = (
        f'Obra: {obra.titulo} (versión: {obra.get_tipo_display()})\n\n'
        f'Unidades (id | tipo | nombre | orden):\n{lineas}'
    )
    parte = (
        f'Parte indicada por el autor: id={referencia.id} ({etiqueta_unidad(referencia)}).'
        if referencia else 'El autor no ha indicado la parte: proponla en parte_id.'
    )
    peticion = f'{parte}\n\nTexto de la publicación:\n"""{texto}"""'

    modelo = modelo or modelo_fronteras()
    response = llamar_claude(
        funcion,
        usuario=usuario,
        obra=obra,
        timeout=timeout,
        model=modelo,
        system=SYSTEM_PROMPT,
        tools=[HERRAMIENTA],
        messages=[{'role': 'user', 'content': [
            # La obra y sus unidades se repiten entre publicaciones: van en caché.
            {'type': 'text', 'text': contexto_obra, 'cache_control': {'type': 'ephemeral'}},
            {'type': 'text', 'text': peticion},
        ]}],
        **_parametros_modelo(modelo),
    )

    bloque = next((b for b in response.content if b.type == 'tool_use'), None)
    if bloque is None:
        raise RespuestaInvalida('la respuesta no incluyó una clasificación.')

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
        raise RespuestaInvalida(f'id inexistente o excluido: {valor}')
    return unidad


def _resolver(entrada, unidades_por_id, referencia):
    """Frontera = la revelación más tardía, nunca anterior a la parte. Confianza = la mínima.
    Un formato inválido o un id inventado invalida toda la propuesta: lo descartado podría ser
    justo la revelación más tardía. Si la IA elige por su cuenta una unidad sin título, la confianza
    se limita por debajo del umbral: no se aplica sola al publicar y la interfaz avisa de certeza baja."""
    if not isinstance(entrada, dict):
        raise RespuestaInvalida('la clasificación no es un objeto.')
    crudas = entrada.get('revelaciones') or []
    if not isinstance(crudas, list) or not all(isinstance(r, dict) for r in crudas):
        raise RespuestaInvalida('revelaciones con formato inválido.')

    parte = referencia or _unidad(unidades_por_id, entrada.get('parte_id'))
    revelaciones = []
    for r in crudas[:MAX_REVELACIONES]:
        hecho = ' '.join(str(r.get('hecho') or '').split())[:200]
        if hecho:
            revelaciones.append(
                Revelacion(hecho, _unidad(unidades_por_id, r.get('unidad_id')), _acotar(r.get('confianza')))
            )
    revelaciones.sort(key=lambda r: r.unidad.orden_fin)

    confianza = min([_acotar(entrada.get('confianza'))] + [r.confianza for r in revelaciones])
    frontera = max([parte] + [r.unidad for r in revelaciones], key=lambda u: u.orden_fin)
    elegida_por_ia = referencia is None or frontera.id != referencia.id
    if elegida_por_ia and es_nombre_generico(frontera):
        confianza = min(confianza, CONFIANZA_MAX_SIN_NOMBRE)
    return SugerenciaIA(frontera, confianza, parte, revelaciones)