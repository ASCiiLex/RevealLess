from django.db import migrations

TIPO_PREVIO = 'previo'


def _orden_frontera(unidad):
    # Copia histórica de UnidadNarrativa.orden_frontera.
    if unidad.tipo == TIPO_PREVIO:
        return max(unidad.orden_inicio - 1, 0)
    return unidad.orden_fin


def elevar(apps, schema_editor):
    """Posts cuya frontera quedó por debajo de la primera unidad de alguno de sus temas."""
    Post = apps.get_model('posts', 'Post')
    posts = (
        Post.objects.filter(temas_transversales__unidades__isnull=False, frontera_spoiler__isnull=False)
        .select_related('frontera_spoiler').distinct()
    )
    for post in posts:
        frontera = post.frontera_spoiler
        for tema in post.temas_transversales.all():
            primera = tema.unidades.order_by('orden_fin').first()
            if primera and _orden_frontera(frontera) < _orden_frontera(primera):
                frontera = primera
        if frontera.pk != post.frontera_spoiler_id:
            Post.objects.filter(pk=post.pk).update(frontera_spoiler=frontera, frontera_orden=_orden_frontera(frontera))


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0014_frontera_minima_referencia'),
        ('narrative', '0023_refrescar_progresos'),
    ]

    operations = [
        migrations.RunPython(elevar, migrations.RunPython.noop),
    ]