def datos_clasificacion(comment):
    """Campos narrativos comunes a las respuestas de crear y editar."""
    return {
        'emocion_autor': comment.emocion_autor,
        'referencia_narrativa_id': comment.referencia_narrativa_id,
        'frontera_spoiler_id': comment.frontera_spoiler_id,
        'frontera_origen': comment.frontera_origen,
        'obra_cruzada_id': comment.obra_cruzada_id,
        'frontera_cruzada_id': comment.frontera_cruzada_id,
    }