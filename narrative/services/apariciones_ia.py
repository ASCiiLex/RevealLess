"""Haiku propone la primera aparición de personajes entre las unidades reales de una obra.
Siempre como propuesta pendiente de revisión: asistente, no oráculo."""

import json
import os

from ..ai_assistant import MODELO_IA

TIMEOUT_SEGUNDOS = 120
MAX_TOKENS = 4000

SYSTEM_PROMPT = (
    'Eres el asistente de catalogación anti-spoiler de RevealLess. Para cada personaje, elige '
    'de la lista de unidades narrativas de la obra aquella en la que aparece por primera vez, '
    'según el orden de publicación de esta obra concreta. Reglas: '
    '1) Nunca elijas una unidad anterior a la real: si dudas, elige una posterior o la unidad '
    'mayor (arco, temporada, saga) que contiene la aparición; el personaje solo se mostrará al '
    'terminarla, y eso es seguro. '
    '2) Si no conoces al personaje en esta obra, devuelve unidad_id null. '
    '3) En "nombre" indica cómo se le conoce en España en su primera aparición, sin revelar '
    'identidades, títulos ni parentescos que se descubran después. '
    '4) Usa solo ids de la lista. "motivo" en una frase, sin spoilers.'
)

TOOL = {
    'name': 'registrar_apariciones',
    'description': 'Registra la primera aparición propuesta para cada personaje recibido, por id.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'apariciones': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'unidad_id': {'type': ['integer', 'null']},
                        'confianza': {'type': 'number', 'description': 'Entre 0 y 1.'},
                        'nombre': {'type': 'string'},
                        'motivo': {'type': 'string'},
                    },
                    'required': ['id', 'unidad_id', 'confianza'],
                },
            },
        },
        'required': ['apariciones'],
    },
}


class ErrorApariciones(Exception):
    pass


def arbol_como_texto(unidades):
    """Una línea por unidad, sangrada por profundidad: 'id: [tipo] nombre'."""
    por_id = {u.id: u for u in unidades}

    def profundidad(unidad):
        nivel = 0
        while unidad.padre_id in por_id:
            unidad = por_id[unidad.padre_id]
            nivel += 1
        return nivel

    return '\n'.join(f'{"  " * profundidad(u)}{u.id}: [{u.tipo}] {u.nombre}' for u in unidades)


def extraer_propuestas(entrada, ids_personajes, ids_unidades):
    """Solo personajes pedidos y unidades reales de la obra; lo demás se descarta."""
    resultado = {}
    for item in entrada.get('apariciones') or []:
        try:
            pid = int(item['id'])
            uid = int(item['unidad_id']) if item.get('unidad_id') is not None else None
            confianza = max(0.0, min(1.0, float(item.get('confianza', 0))))
        except (KeyError, TypeError, ValueError):
            continue
        if pid not in ids_personajes or uid not in ids_unidades:
            continue
        resultado[pid] = {
            'unidad_id': uid,
            'confianza': confianza,
            'nombre': str(item.get('nombre') or '').strip()[:150],
            'nota': str(item.get('motivo') or '').strip()[:300],
        }
    return resultado


def proponer_primeras_apariciones(obra, personajes, unidades):
    """personajes: {id: nombre}. unidades: UnidadNarrativa de la obra por orden_inicio.
    → {id: {unidad_id, confianza, nombre, nota}}. Lanza ErrorApariciones ante fallos de la API."""
    if not personajes:
        return {}

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ErrorApariciones('ANTHROPIC_API_KEY no configurada.')

    import anthropic

    lista = [{'id': pid, 'nombre': nombre} for pid, nombre in personajes.items()]
    contenido = (
        f'Obra: {obra.titulo} ({obra.get_tipo_display()}).\n\n'
        f'Unidades narrativas, en orden de publicación:\n{arbol_como_texto(unidades)}\n\n'
        f'Personajes:\n{json.dumps(lista, ensure_ascii=False)}'
    )
    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_SEGUNDOS)
        response = client.messages.create(
            model=MODELO_IA,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=[TOOL],
            tool_choice={'type': 'tool', 'name': TOOL['name']},
            messages=[{'role': 'user', 'content': contenido}],
        )
    except anthropic.APIError as e:
        raise ErrorApariciones(str(e)) from e

    bloque = next((b for b in response.content if b.type == 'tool_use'), None)
    if bloque is None:
        raise ErrorApariciones('La respuesta no incluyó apariciones.')

    return extraer_propuestas(bloque.input, set(personajes), {u.id for u in unidades})