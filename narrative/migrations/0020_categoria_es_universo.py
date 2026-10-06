from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('narrative', '0019_etapa_nivel'),
    ]

    operations = [
        migrations.AddField(
            model_name='categoria',
            name='es_universo',
            field=models.BooleanField(
                default=False,
                verbose_name='Es un universo',
                help_text='Las obras de esta categoría se muestran como relacionadas entre sí.',
            ),
        ),
    ]