import io
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from PIL import Image

from core.imagenes.optimizacion import medir_imagen
from narrative.serializers import PostSerializer
from .utils import crear_obra, crear_post


def _jpeg(ancho, alto, orientacion=None):
    buffer = io.BytesIO()
    exif = Image.Exif()
    if orientacion:
        exif[0x0112] = orientacion
    Image.new('RGB', (ancho, alto), 'green').save(buffer, 'JPEG', exif=exif)
    return buffer.getvalue()


class MedirImagenTests(SimpleTestCase):
    def test_medidas_tal_cual(self):
        self.assertEqual(medir_imagen(_jpeg(300, 200)), (300, 200))

    def test_orientacion_girada_intercambia_ancho_y_alto(self):
        self.assertEqual(medir_imagen(_jpeg(300, 200, orientacion=6)), (200, 300))

    def test_si_no_es_imagen_devuelve_none(self):
        self.assertIsNone(medir_imagen(b'no soy una imagen'))


class DimensionesAlGuardarTests(TestCase):
    def setUp(self):
        # Las imágenes de prueba no tocan la carpeta media real.
        media = tempfile.TemporaryDirectory()
        self.addCleanup(media.cleanup)
        ajuste = override_settings(MEDIA_ROOT=media.name)
        ajuste.enable()
        self.addCleanup(ajuste.disable)

        autor = User.objects.create_user('autor_dimensiones', password='x')
        obra, (unidad,) = crear_obra('imagen-dimensiones')
        self.post = crear_post(autor, obra, unidad)

    def test_guarda_las_medidas_al_subir_y_la_api_las_devuelve(self):
        self.post.image = SimpleUploadedFile('foto.jpg', _jpeg(300, 200), content_type='image/jpeg')
        self.post.save()

        self.post.refresh_from_db()
        self.assertEqual((self.post.imagen_ancho, self.post.imagen_alto), (300, 200))
        datos = PostSerializer(self.post).data
        self.assertEqual((datos['imagen_ancho'], datos['imagen_alto']), (300, 200))

    def test_sin_imagen_no_hay_medidas(self):
        self.assertEqual((self.post.imagen_ancho, self.post.imagen_alto), (None, None))