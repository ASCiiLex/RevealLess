"""Traducción al español de textos del catálogo con Haiku (tool_use → JSON validado por id)."""

import json
import os

from ..ai_assistant import MODELO_IA

TIMEOUT_SEGUNDOS = 90
MAX_TOKENS = 8000

SYSTEM_PROMPT = (
    'Traduces al español de España títulos de capítulos y sinopsis de obras de ficción '
    '(anime, manga, series, películas y libros). Conserva los nombres propios, técnicas '
    'y términos de la obra como los usa su traducción oficial en español si la conoces; '
    'si no, déjalos en el original. No añadas, resumas ni reveles información que no esté '
    'en el texto. Si un texto ya está en español, devuélvelo sin cambios. Devuelve '
    'exactamente un elemento por cada id recibido.'
)

TOOL = {
    'name': 'registrar_traducciones',
    'description': 'Registra la traducción al español de cada texto recibido, por id.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'traducciones': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'texto': {'type': 'string'},
                    },
                    'required': ['id', 'texto'],
                },
            },
        },
        'required': ['traducciones'],
    },
}


class ErrorTraduccion(Exception):
    pass


def extraer_traducciones(entrada, ids_validos):
    """Solo ids pedidos y textos no vacíos: lo demás se descarta sin tocar la BD."""
    resultado = {}
    for item in entrada.get('traducciones') or []:
        try:
            id_ = int(item['id'])
        except (KeyError, TypeError, ValueError):
            continue
        texto = str(item.get('texto') or '').strip()
        if id_ in ids_validos and texto:
            resultado[id_] = texto
    return resultado


def traducir_textos(textos):
    """{id: texto} → {id: traducción}. Lanza ErrorTraduccion ante cualquier fallo de la API."""
    if not textos:
        return {}

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ErrorTraduccion('ANTHROPIC_API_KEY no configurada.')

    import anthropic

    entrada = [{'id': id_, 'texto': texto} for id_, texto in textos.items()]
    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_SEGUNDOS)
        response = client.messages.create(
            model=MODELO_IA,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=[TOOL],
            tool_choice={'type': 'tool', 'name': TOOL['name']},
            messages=[{
                'role': 'user',
                'content': 'Traduce estos textos:\n' + json.dumps(entrada, ensure_ascii=False),
            }],
        )
    except anthropic.APIError as e:
        raise ErrorTraduccion(str(e)) from e

    bloque = next((b for b in response.content if b.type == 'tool_use'), None)
    if bloque is None:
        raise ErrorTraduccion('La respuesta no incluyó traducciones.')

    return extraer_traducciones(bloque.input, set(textos))