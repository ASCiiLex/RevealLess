import io
import tempfile
from io import StringIO

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from PIL import Image

from core.imagenes.miniaturas import (
    LADO_MINIATURA, VARIANTES, generar_miniatura, generar_variante, nombre_miniatura, nombre_variante,
)
from narrative.models import Obra


def _png(ancho, alto):
    buffer = io.BytesIO()
    Image.new('RGB', (ancho, alto), 'blue').save(buffer, 'PNG')
    return buffer.getvalue()


class GenerarVarianteTests(SimpleTestCase):
    def test_miniatura_en_webp_del_lado_maximo(self):
        imagen = Image.open(io.BytesIO(generar_miniatura(_png(1000, 500))))
        self.assertEqual(imagen.format, 'WEBP')
        self.assertEqual(max(imagen.size), LADO_MINIATURA)

    def test_variante_media_de_900(self):
        imagen = Image.open(io.BytesIO(generar_variante(_png(1600, 800), VARIANTES['med'])))
        self.assertEqual(max(imagen.size), VARIANTES['med'])

    def test_no_amplia_las_pequenas(self):
        imagen = Image.open(io.BytesIO(generar_variante(_png(300, 200), VARIANTES['med'])))
        self.assertEqual(imagen.size, (300, 200))

    def test_si_no_es_imagen_devuelve_el_original(self):
        self.assertEqual(generar_miniatura(b'no soy una imagen'), b'no soy una imagen')

    def test_nombres_junto_al_original(self):
        self.assertEqual(nombre_miniatura('narrative/obras/x/portada.jpg'), 'narrative/obras/x/portada.min.webp')
        self.assertEqual(nombre_variante('narrative/obras/x/portada.jpg', 'med'), 'narrative/obras/x/portada.med.webp')


class VariantesAlGuardarTests(TestCase):
    def setUp(self):
        # Las imágenes de prueba no tocan la carpeta media real.
        media = tempfile.TemporaryDirectory()
        self.addCleanup(media.cleanup)
        ajuste = override_settings(MEDIA_ROOT=media.name)
        ajuste.enable()
        self.addCleanup(ajuste.disable)

    def _obra_con_portada(self):
        return Obra.objects.create(
            titulo='Con portada', slug='con-portada',
            imagen=SimpleUploadedFile('portada.png', _png(1000, 500), content_type='image/png'),
        )

    def test_crea_todas_las_variantes_al_subir(self):
        obra = self._obra_con_portada()
        for variante in VARIANTES:
            self.assertTrue(default_storage.exists(nombre_variante(obra.imagen.name, variante)))
        self.assertTrue(obra.miniatura_url.endswith('.min.webp'))

    def test_sin_imagen_usa_la_de_por_defecto(self):
        obra = Obra.objects.create(titulo='Sin portada', slug='sin-portada')
        self.assertEqual(obra.miniatura_url, Obra.IMAGEN_POR_DEFECTO_GENERICA)

    def test_el_comando_crea_las_que_faltan(self):
        obra = self._obra_con_portada()
        media = nombre_variante(obra.imagen.name, 'med')
        default_storage.delete(media)

        call_command('generar_miniaturas', stdout=StringIO())

        self.assertTrue(default_storage.exists(media))