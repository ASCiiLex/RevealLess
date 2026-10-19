from django.db import migrations

TIPO_PREVIO = 'previo'


def _orden_frontera(unidad):
    # Copia histórica de UnidadNarrativa.orden_frontera.
    if unidad.tipo == TIPO_PREVIO:
        return max(unidad.orden_inicio - 1, 0)
    return unidad.orden_fin


def elevar(apps, schema_editor):
    """Posts cuya frontera quedó por debajo del primer episodio de su referencia."""
    Unidad = apps.get_model('narrative', 'UnidadNarrativa')
    Post = apps.get_model('posts', 'Post')
    posts = Post.objects.filter(
        referencia_narrativa__isnull=False, frontera_spoiler__isnull=False,
    ).select_related('referencia_narrativa', 'frontera_spoiler')
    for post in posts:
        referencia = post.referencia_narrativa
        primera_hoja = Unidad.objects.filter(
            obra_id=referencia.obra_id, orden_inicio=referencia.orden_inicio, hijos__isnull=True,
        ).first()
        if primera_hoja and _orden_frontera(post.frontera_spoiler) < _orden_frontera(primera_hoja):
            Post.objects.filter(pk=post.pk).update(
                frontera_spoiler=primera_hoja, frontera_orden=_orden_frontera(primera_hoja),
            )


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0013_recalcular_fronteras'),
    ]

    operations = [
        migrations.RunPython(elevar, migrations.RunPython.noop),
    ]