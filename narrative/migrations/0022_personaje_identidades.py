import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('narrative', '0021_solicitudpersonaje'),
    ]

    operations = [
        migrations.AddField(
            model_name='personaje',
            name='identidad_de',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='otras_identidades', to='narrative.personaje',
                verbose_name='Es otra identidad de',
                help_text='Disfraz o identidad con ficha propia (ej. Sogeking → Usopp). Cada uno mantiene su ficha y su feed.',
            ),
        ),
        migrations.AddField(
            model_name='personaje',
            name='identidad_revelada_tras',
            field=models.ManyToManyField(
                blank=True, related_name='identidades_reveladas', to='narrative.unidadnarrativa',
                verbose_name='Se sabe desde',
                help_text='Unidades tras las que se conoce el vínculo (una por obra si hace falta). Vacío: desde su primera aparición.',
            ),
        ),
    ]