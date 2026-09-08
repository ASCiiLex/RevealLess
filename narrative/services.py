def calcular_orden_absoluto(unidad):
    """Progreso conservador a nivel de bloque: si no es hoja, se asume que
    todavía no se ha consumido nada de ese bloque."""
    if unidad.es_hoja:
        return unidad.orden_inicio
    return max(unidad.orden_inicio - 1, 0)


def actualizar_progreso(usuario, obra, nueva_unidad):
    from .models import ProgresoUsuario

    nuevo_orden = calcular_orden_absoluto(nueva_unidad)

    progreso, creado = ProgresoUsuario.objects.get_or_create(
        usuario=usuario,
        obra=obra,
        defaults={'unidad_actual': nueva_unidad, 'orden_absoluto': nuevo_orden},
    )
    if creado:
        return progreso

    if nuevo_orden < progreso.orden_absoluto:
        raise ValueError('El progreso no puede retroceder.')

    progreso.unidad_actual = nueva_unidad
    progreso.orden_absoluto = nuevo_orden
    progreso.save(update_fields=['unidad_actual', 'orden_absoluto'])
    return progreso