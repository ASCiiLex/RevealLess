import logging
import os

logger = logging.getLogger(__name__)

CONFIANZA_MINIMA = 0.6
MODELO_IA = 'claude-haiku-4-5-20251001'
TIMEOUT_SEGUNDOS = 8


class SugerenciaIA:
    def __init__(self, frontera_spoiler=None, confianza=0.0):
        self.frontera_spoiler = frontera_spoiler
        self.confianza = confianza

    @property
    def es_utilizable(self):
        return self.frontera_spoiler is not None and self.confianza >= CONFIANZA_MINIMA


def proponer_clasificacion(texto, obra, unidad_autor, referencia=None):
    """Punto único de entrada al asistente de IA. Nunca lanza excepción hacia
    fuera: cualquier fallo (API caída, timeout, sin API key, id inventado)
    se traduce en una sugerencia no utilizable, y quien llama cae al
    fallback (progreso del autor) sin bloquear la publicación."""
    try:
        return _llamar_api(texto, obra, unidad_autor, referencia)
    except Exception:
        logger.exception('Fallo al llamar a la API de IA de clasificación')
        return SugerenciaIA()


def _llamar_api(texto, obra, unidad_autor, referencia):
    from .models import UnidadNarrativa

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise RuntimeError('ANTHROPIC_API_KEY no configurada.')

    import anthropic

    unidades = list(
        UnidadNarrativa.objects.filter(obra=obra).order_by('orden_inicio')
    )
    if not unidades:
        raise RuntimeError('La obra no tiene unidades narrativas.')

    unidades_por_id = {u.id: u for u in unidades}
    candidatas = [
        {
            'id': u.id,
            'nombre': u.nombre,
            'tipo': u.tipo,
            'orden_inicio': u.orden_inicio,
            'orden_fin': u.orden_fin,
        }
        for u in unidades
    ]

    system_prompt = (
        'Eres el asistente de clasificación anti-spoiler de RevealLess. '
        'Dado el texto de una publicación y la lista de unidades narrativas '
        'de la obra (ordenadas por posición de consumo), debes elegir la '
        'unidad que debería usarse como frontera de spoiler: el punto hasta '
        'el que un lector debe haber llegado para leer este texto sin '
        'riesgo de spoiler. Elige la unidad más concreta posible (un episodio '
        'o capítulo antes que un arco completo) que cubra todo lo que el texto '
        'revela; no elijas el final de un arco si lo descrito ocurre antes. '
        'Nunca elijas una unidad anterior a la parte de la que habla la '
        'publicación. Si el texto no revela nada más allá de esa parte, elige '
        'esa misma parte. Nunca elijas una unidad con un id que no esté en la '
        'lista proporcionada.'
    )

    parte = (
        f'Parte de la que habla la publicación: id={referencia.id} '
        f'({referencia.nombre}, orden_fin={referencia.orden_fin}).\n'
        if referencia else ''
    )
    user_prompt = (
        f'Posición actual del autor: id={unidad_autor.id} '
        f'({unidad_autor.nombre}, orden_fin={unidad_autor.orden_fin}).\n'
        f'{parte}\n'
        f'Unidades narrativas disponibles:\n{candidatas}\n\n'
        f'Texto de la publicación:\n"""{texto}"""'
    )

    tools = [{
        'name': 'clasificar_frontera',
        'description': (
            'Registra la unidad narrativa elegida como frontera de spoiler '
            'y la confianza de esa elección.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'unidad_id': {
                    'type': 'integer',
                    'description': 'id de la unidad elegida, debe estar en la lista dada',
                },
                'confianza': {
                    'type': 'number',
                    'description': 'confianza de la clasificación, entre 0 y 1',
                },
            },
            'required': ['unidad_id', 'confianza'],
        },
    }]

    client = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_SEGUNDOS)
    response = client.messages.create(
        model=MODELO_IA,
        max_tokens=200,
        system=system_prompt,
        tools=tools,
        tool_choice={'type': 'tool', 'name': 'clasificar_frontera'},
        messages=[{'role': 'user', 'content': user_prompt}],
    )

    bloque = next(
        (b for b in response.content if b.type == 'tool_use'), None
    )
    if bloque is None:
        raise RuntimeError('La respuesta de la IA no incluyó una clasificación.')

    unidad_id = bloque.input.get('unidad_id')
    confianza = float(bloque.input.get('confianza', 0))
    confianza = max(0.0, min(1.0, confianza))

    unidad = unidades_por_id.get(unidad_id)
    if unidad is None:
        raise RuntimeError(f'La IA propuso un id inexistente: {unidad_id}')

    return SugerenciaIA(frontera_spoiler=unidad, confianza=confianza)