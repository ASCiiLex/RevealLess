import core.validators
import django.core.validators
import django.db.models.deletion
import posts.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('narrative', '0020_categoria_es_universo'),
        ('posts', '0009_post_personajes'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='disposicion',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', 'Automática'),
                    ('lado', 'Lado a lado'),
                    ('apiladas', 'Apiladas'),
                    ('deslizador', 'Antes / después'),
                    ('destacada', 'Una destacada'),
                    ('fila', 'En fila'),
                    ('cuadricula', 'Cuadrícula'),
                ],
                default='',
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name='PostImagen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagen', models.ImageField(
                    upload_to=posts.models.post_galeria_path,
                    validators=[
                        django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
                        core.validators.validate_image_size,
                    ],
                )),
                ('etiqueta', models.CharField(blank=True, max_length=40)),
                ('orden', models.PositiveSmallIntegerField(default=0)),
                ('post', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='imagenes', to='posts.post',
                )),
            ],
            options={
                'verbose_name': 'Imagen de post',
                'verbose_name_plural': 'Imágenes de post',
                'ordering': ['orden'],
            },
        ),
        migrations.CreateModel(
            name='PersonajeComparado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orden', models.PositiveSmallIntegerField(default=0)),
                ('personaje', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='comparaciones', to='narrative.personaje',
                )),
                ('post', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='comparaciones', to='posts.post',
                )),
            ],
            options={
                'verbose_name': 'Personaje comparado',
                'verbose_name_plural': 'Personajes comparados',
                'ordering': ['orden'],
                'constraints': [
                    models.UniqueConstraint(fields=('post', 'personaje'), name='uniq_personaje_comparado_post'),
                ],
            },
        ),
        migrations.AddField(
            model_name='post',
            name='personajes_comparados',
            field=models.ManyToManyField(
                blank=True,
                related_name='posts_comparados',
                through='posts.PersonajeComparado',
                to='narrative.personaje',
            ),
        ),
    ]