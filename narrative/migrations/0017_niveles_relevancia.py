from django.db import migrations, models

# Niveles antiguos (1-3) a la escala espaciada.
ANTERIOR_A_NUEVO = {3: 50, 2: 40, 1: 20}


def convertir(apps, schema_editor):
    Relevancia = apps.get_model('narrative', 'RelevanciaPersonaje')
    for anterior, nuevo in ANTERIOR_A_NUEVO.items():
        Relevancia.objects.filter(nivel=anterior).update(nivel=nuevo)


def revertir(apps, schema_editor):
    Relevancia = apps.get_model('narrative', 'RelevanciaPersonaje')
    # Los niveles nuevos se pliegan al más cercano de la escala antigua.
    Relevancia.objects.filter(nivel=10).update(nivel=1)
    Relevancia.objects.filter(nivel=30).update(nivel=2)
    for anterior, nuevo in ANTERIOR_A_NUEVO.items():
        Relevancia.objects.filter(nivel=nuevo).update(nivel=anterior)


class Migration(migrations.Migration):

    dependencies = [
        ('narrative', '0016_relevancia_personaje'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relevanciapersonaje',
            name='nivel',
            field=models.PositiveSmallIntegerField(
                choices=[
                    (50, 'Protagonista'),
                    (40, 'Principal'),
                    (30, 'Destacado'),
                    (20, 'Secundario'),
                    (10, 'Episódico'),
                ],
                default=40,
            ),
        ),
        migrations.RunPython(convertir, revertir),
    ]