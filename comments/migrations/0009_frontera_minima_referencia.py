from django.db import migrations

TIPO_PREVIO = 'previo'
HEREDADO = 'heredado_post'
EXPLICITO = 'explicito'


def _orden_frontera(unidad):
    # Copia histórica de UnidadNarrativa.orden_frontera.
    if unidad.tipo == TIPO_PREVIO:
        return max(unidad.orden_inicio - 1, 0)
    return unidad.orden_fin


def ajustar(apps, schema_editor):
    """Comentarios que se leían antes del comienzo de su referencia: heredados que la superan
    pasan a frontera propia; los propios por debajo se elevan."""
    Unidad = apps.get_model('narrative', 'UnidadNarrativa')
    Comment = apps.get_model('comments', 'Comment')
    comentarios = Comment.objects.filter(referencia_narrativa__isnull=False).select_related(
        'referencia_narrativa', 'frontera_spoiler', 'post',
    )
    for comment in comentarios:
        referencia = comment.referencia_narrativa
        hoja = Unidad.objects.filter(
            obra_id=referencia.obra_id, orden_inicio=referencia.orden_inicio, hijos__isnull=True,
        ).first()
        if hoja is None:
            continue
        minimo = _orden_frontera(hoja)
        if comment.frontera_origen == HEREDADO:
            if minimo > (comment.post.frontera_orden or 0):
                Comment.objects.filter(pk=comment.pk).update(
                    frontera_spoiler=hoja, frontera_orden=minimo, frontera_origen=EXPLICITO,
                )
        elif comment.frontera_spoiler_id and _orden_frontera(comment.frontera_spoiler) < minimo:
            Comment.objects.filter(pk=comment.pk).update(frontera_spoiler=hoja, frontera_orden=minimo)


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0008_recalcular_fronteras'),
        # La frontera de los posts ya corregida: los heredados se comparan con ella.
        ('posts', '0014_frontera_minima_referencia'),
    ]

    operations = [
        migrations.RunPython(ajustar, migrations.RunPython.noop),
    ]