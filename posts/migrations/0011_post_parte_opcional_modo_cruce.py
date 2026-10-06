import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('narrative', '0021_solicitudpersonaje'),
        ('posts', '0010_post_comparativa_galeria'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='referencia_narrativa',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='%(class)s_referenciados', to='narrative.unidadnarrativa',
            ),
        ),
        migrations.AddField(
            model_name='post',
            name='modo_cruce',
            field=models.CharField(
                choices=[
                    ('comparativa', 'Comparativa: ambas fronteras'),
                    ('misma_escena', 'Misma escena: basta una frontera'),
                ],
                default='comparativa',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='personajecomparado',
            name='personaje',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name='comparaciones', to='narrative.personaje',
            ),
        ),
        migrations.AddField(
            model_name='personajecomparado',
            name='solicitud',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='comparaciones', to='narrative.solicitudpersonaje',
            ),
        ),
    ]