from django.db import migrations, models

import posts.models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0016_post_imagen_dimensiones'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='video_youtube_id',
            field=models.CharField(blank=True, max_length=11, verbose_name='Vídeo de YouTube'),
        ),
        migrations.AddField(
            model_name='post',
            name='video_titulo',
            field=models.CharField(blank=True, max_length=200, verbose_name='Título del vídeo'),
        ),
        migrations.AddField(
            model_name='post',
            name='video_canal',
            field=models.CharField(blank=True, max_length=150, verbose_name='Canal del vídeo'),
        ),
        migrations.AddField(
            model_name='post',
            name='video_portada',
            field=models.ImageField(
                blank=True, null=True, upload_to=posts.models.post_video_path, verbose_name='Portada del vídeo',
            ),
        ),
    ]