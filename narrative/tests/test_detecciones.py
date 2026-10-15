from django.test import TestCase

from narrative.models import Obra
from narrative.services.detecciones import serializar_detecciones
from posts.tests.utils import crear_obra


class SerializarDeteccionesTests(TestCase):
    def setUp(self):
        self.anime, _ = crear_obra('anime-det', 1)
        self.manga, _ = crear_obra('manga-det', 1, tipo_unidad='capitulo', tipo=Obra.TIPO_MANGA, adapta_a=self.anime)
        self.otra, _ = crear_obra('otra-det', 1)

    def test_marca_las_adaptaciones_como_misma_historia(self):
        datos = serializar_detecciones(
            [{'obra': self.manga, 'palabra': 'manga'}, {'obra': self.otra, 'palabra': 'otra'}], self.anime,
        )
        self.assertEqual([d['misma_historia'] for d in datos], [True, False])

    def test_sin_obra_principal_no_ofrece_misma_escena(self):
        datos = serializar_detecciones([{'obra': self.manga, 'palabra': 'manga'}])
        self.assertFalse(datos[0]['misma_historia'])