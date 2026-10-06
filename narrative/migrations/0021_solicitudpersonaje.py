import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('narrative', '0020_categoria_es_universo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SolicitudPersonaje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=150)),
                ('estado', models.CharField(
                    choices=[('pendiente', 'Pendiente'), ('aprobada', 'Aprobada'), ('rechazada', 'Rechazada')],
                    default='pendiente', max_length=20,
                )),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('resuelto_en', models.DateTimeField(blank=True, null=True)),
                ('obra', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='solicitudes_personaje',
                    to='narrative.obra',
                )),
                ('personaje', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='solicitudes', to='narrative.personaje',
                    help_text='Vacío: se crea al aprobar (o se reutiliza uno con el mismo nombre). Elige uno si es el mismo con otro nombre.',
                )),
                ('unidad', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='solicitudes_personaje',
                    to='narrative.unidadnarrativa',
                    help_text='Primera aparición. Se propone la frontera del post: corrígela antes de aprobar si hace falta.',
                )),
                ('usuario', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='solicitudes_personaje',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Solicitud de personaje',
                'verbose_name_plural': 'Solicitudes de personaje',
                'ordering': ['-creado_en'],
            },
        ),
    ]