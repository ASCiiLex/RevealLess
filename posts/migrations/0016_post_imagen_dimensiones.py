from io import BytesIO

from django.db import migrations, models

ORIENTACIONES_GIRADAS = {5, 6, 7, 8}
ETIQUETA_ORIENTACION = 0x0112


def _medir(datos):
    # Copia de core.imagenes.optimizacion.medir_imagen: una migración no depende del código vivo.
    from PIL import Image

    imagen = Image.open(BytesIO(datos))
    ancho, alto = imagen.size
    if imagen.getexif().get(ETIQUETA_ORIENTACION) in ORIENTACIONES_GIRADAS:
        return alto, ancho
    return ancho, alto


def rellenar_dimensiones(apps, schema_editor):
    """Medidas de las fotos ya publicadas. Si alguna no se puede leer, queda sin medidas
    y la tarjeta usa la proporción por defecto."""
    Post = apps.get_model('posts', 'Post')
    storage = Post._meta.get_field('image').storage
    pendientes = Post.objects.exclude(image='').exclude(image__isnull=True).values_list('id', 'image')
    for post_id, nombre in pendientes:
        try:
            with storage.open(nombre, 'rb') as archivo:
                ancho, alto = _medir(archivo.read())
        except Exception:
            continue
        Post.objects.filter(id=post_id).update(imagen_ancho=ancho, imagen_alto=alto)


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0015_frontera_minima_temas'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='imagen_ancho',
            field=models.PositiveIntegerField(blank=True, editable=False, null=True, verbose_name='Ancho de la imagen'),
        ),
        migrations.AddField(
            model_name='post',
            name='imagen_alto',
            field=models.PositiveIntegerField(blank=True, editable=False, null=True, verbose_name='Alto de la imagen'),
        ),
        migrations.RunPython(rellenar_dimensiones, migrations.RunPython.noop),
    ]