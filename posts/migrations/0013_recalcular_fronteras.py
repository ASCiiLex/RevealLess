from django.db import migrations, models
from django.db.models import Case, F, OuterRef, Subquery, Value, When
from django.db.models.functions import Greatest

TIPO_PREVIO = 'previo'


def _orden(Unidad, campo):
    # Copia histórica de expresion_orden_frontera(): las migraciones no importan código vivo.
    return Subquery(
        Unidad.objects.filter(pk=OuterRef(campo)).annotate(
            posicion=Case(
                When(
                    tipo=TIPO_PREVIO,
                    then=Greatest(F('orden_inicio') - 1, Value(0), output_field=models.IntegerField()),
                ),
                default=F('orden_fin'),
                output_field=models.IntegerField(),
            )
        ).values('posicion')[:1]
    )


def recalcular(apps, schema_editor):
    """El previo pasa a exigir la posición anterior; además corrige cachés desfasadas."""
    Unidad = apps.get_model('narrative', 'UnidadNarrativa')
    Post = apps.get_model('posts', 'Post')
    Post.objects.filter(frontera_spoiler__isnull=False).update(
        frontera_orden=_orden(Unidad, 'frontera_spoiler'),
    )
    Post.objects.filter(frontera_cruzada__isnull=False).update(
        frontera_cruzada_orden=_orden(Unidad, 'frontera_cruzada'),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0012_postimagen_encuadre'),
        ('narrative', '0022_personaje_identidades'),
    ]

    operations = [
        migrations.RunPython(recalcular, migrations.RunPython.noop),
    ]