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
    """Heredados sin frontera_spoiler quedan fuera: siguen tomando la de su post."""
    Unidad = apps.get_model('narrative', 'UnidadNarrativa')
    Comment = apps.get_model('comments', 'Comment')
    Comment.objects.filter(frontera_spoiler__isnull=False).update(
        frontera_orden=_orden(Unidad, 'frontera_spoiler'),
    )
    Comment.objects.filter(frontera_cruzada__isnull=False).update(
        frontera_cruzada_orden=_orden(Unidad, 'frontera_cruzada'),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0007_alter_commentreaction_reaction'),
        ('narrative', '0022_personaje_identidades'),
    ]

    operations = [
        migrations.RunPython(recalcular, migrations.RunPython.noop),
    ]