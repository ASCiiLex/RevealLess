from django.db import migrations, models
from django.utils import timezone


def crear_propuestas_de_apariciones_sueltas(apps, schema_editor):
    """Apariciones añadidas sin propuesta (a mano o por script) pasan a propuesta Manual aprobada."""
    Personaje = apps.get_model('narrative', 'Personaje')
    Propuesta = apps.get_model('narrative', 'PropuestaAparicion')
    existentes = set(Propuesta.objects.values_list('personaje_id', 'unidad_id'))
    ahora = timezone.now()
    nuevas = [
        Propuesta(personaje_id=p, unidad_id=u, origen='manual', estado='aprobada', resuelto_en=ahora)
        for p, u in Personaje.unidades.through.objects.values_list('personaje_id', 'unidadnarrativa_id')
        if (p, u) not in existentes
    ]
    Propuesta.objects.bulk_create(nuevas, batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ('narrative', '0017_niveles_relevancia'),
    ]

    operations = [
        migrations.AlterField(
            model_name='propuestaaparicion',
            name='origen',
            field=models.CharField(
                choices=[('wikidata', 'Wikidata'), ('ia', 'IA (Haiku)'), ('manual', 'Manual')],
                default='manual',
                max_length=20,
            ),
        ),
        migrations.RunPython(crear_propuestas_de_apariciones_sueltas, migrations.RunPython.noop),
    ]