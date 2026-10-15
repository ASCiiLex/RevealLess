def serializar_detecciones(detecciones, obra=None):
    """Formato JSON de detectar_posibles_referencias_cruzadas() para las APIs de publicación.
    misma_historia: el aviso solo ofrece «misma escena» entre adaptaciones de la obra principal."""
    # Import diferido: posts ya depende de narrative.
    from posts.models import misma_historia

    return [
        {
            'obra_id': d['obra'].id,
            'obra_titulo': d['obra'].titulo,
            'obra_slug': d['obra'].slug,
            'palabra': d['palabra'],
            'misma_historia': bool(obra) and misma_historia(obra, d['obra']),
        }
        for d in detecciones
    ]