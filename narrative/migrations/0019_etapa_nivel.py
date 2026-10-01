from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('narrative', '0018_origen_manual_propuestas'),
    ]

    operations = [
        migrations.AddField(
            model_name='etapapersonaje',
            name='nivel',
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                choices=[
                    (50, 'Protagonista'),
                    (40, 'Principal'),
                    (30, 'Destacado'),
                    (20, 'Secundario'),
                    (10, 'Episódico'),
                ],
                help_text='Relevancia en esta obra desde esta etapa (ej. de Secundario a Principal al unirse). Vacío: no cambia.',
            ),
        ),
    ]