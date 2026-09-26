def serializar_detecciones(detecciones):
    """Formato JSON de detectar_posibles_referencias_cruzadas() para las APIs de publicación."""
    return [
        {
            'obra_id': d['obra'].id,
            'obra_titulo': d['obra'].titulo,
            'obra_slug': d['obra'].slug,
            'palabra': d['palabra'],
        }
        for d in detecciones
    ]