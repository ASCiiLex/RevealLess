import shutil
import tempfile
from io import BytesIO, StringIO

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from PIL import Image

from core.imagenes import LADO_MAXIMO, optimizar_imagen
from narrative.models import ClasificacionNarrativa, Obra, UnidadNarrativa
from posts.models import Post


def _jpeg(ancho, alto, exif=None):
    salida = BytesIO()
    opciones = {'exif': exif} if exif else {}
    Image.new('RGB', (ancho, alto), (120, 60, 30)).save(salida, 'JPEG', quality=95, **opciones)
    return salida.getvalue()


def _lado_mayor(datos_o_archivo):
    return max(Image.open(datos_o_archivo).size)


class OptimizarImagenTests(SimpleTestCase):
    def test_imagen_pequena_y_ligera_no_se_toca(self):
        self.assertIsNone(optimizar_imagen(_jpeg(400, 300)))

    def test_imagen_grande_se_reduce_al_lado_maximo(self):
        self.assertEqual(_lado_mayor(BytesIO(optimizar_imagen(_jpeg(3200, 2000)))), LADO_MAXIMO)

    def test_elimina_los_metadatos_exif(self):
        exif = Image.Exif()
        exif[0x010F] = 'Fabricante'
        resultado = optimizar_imagen(_jpeg(3200, 2000, exif.tobytes()))
        self.assertNotIn(0x010F, Image.open(BytesIO(resultado)).getexif())

    def test_lo_que_no_es_imagen_se_ignora(self):
        self.assertIsNone(optimizar_imagen(b'no soy una imagen'))


class ImagenesGuardadasTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        ajustes = override_settings(MEDIA_ROOT=self.media)
        ajustes.enable()
        self.addCleanup(ajustes.disable)
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)

        self.autor = User.objects.create_user('img_autor', password='x')
        self.obra = Obra.objects.create(titulo='Serie Imágenes', slug='serie-imagenes')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()

    def _post(self, **extra):
        return Post.objects.create(
            author=self.autor, obra=self.obra, text='con imagen',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO, **extra,
        )

    def _imagen_antigua(self):
        nombre = default_storage.save('posts/antigua.jpg', ContentFile(_jpeg(3200, 2000)))
        post = self._post()
        # update() no dispara la señal: simula una imagen subida antes de la optimización.
        Post.objects.filter(id=post.id).update(image=nombre)
        return post, nombre

    def test_al_subir_se_optimiza(self):
        post = self._post(image=ContentFile(_jpeg(3200, 2000), name='grande.jpg'))
        with post.image.open('rb') as archivo:
            self.assertEqual(_lado_mayor(archivo), LADO_MAXIMO)

    def test_el_comando_optimiza_las_existentes_sin_cambiar_el_nombre(self):
        post, nombre = self._imagen_antigua()
        call_command('optimizar_imagenes', '--aplicar', stdout=StringIO(), stderr=StringIO())
        post.refresh_from_db()
        self.assertEqual(post.image.name, nombre)
        with default_storage.open(nombre, 'rb') as archivo:
            self.assertEqual(_lado_mayor(archivo), LADO_MAXIMO)

    def test_sin_aplicar_solo_informa(self):
        _, nombre = self._imagen_antigua()
        call_command('optimizar_imagenes', stdout=StringIO(), stderr=StringIO())
        with default_storage.open(nombre, 'rb') as archivo:
            self.assertEqual(_lado_mayor(archivo), 3200)