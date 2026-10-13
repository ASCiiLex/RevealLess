from django.test import SimpleTestCase

from narrative.models import Obra, Personaje
from posts.models import Post


class ImagenPorDefectoTests(SimpleTestCase):
    def _portada(self, tipo):
        return Obra(tipo=tipo).image_url

    def test_pelicula_sin_imagen_usa_su_portada(self):
        self.assertEqual(self._portada(Obra.TIPO_PELICULA), '/static/img/default_pelicula.jpg')

    def test_manga_sin_imagen_usa_su_portada(self):
        self.assertEqual(self._portada(Obra.TIPO_MANGA), '/static/img/default_manga.jpg')

    def test_libro_sin_imagen_usa_su_portada(self):
        self.assertEqual(self._portada(Obra.TIPO_LIBRO), '/static/img/default_libro.jpg')

    def test_serie_sin_imagen_usa_su_portada(self):
        self.assertEqual(self._portada(Obra.TIPO_SERIE), '/static/img/default_serie.jpg')

    def test_ova_sin_imagen_comparte_la_portada_de_serie(self):
        self.assertEqual(self._portada(Obra.TIPO_OVA), '/static/img/default_serie.jpg')

    def test_personaje_sin_imagen_usa_su_portada_propia(self):
        self.assertEqual(Personaje(nombre='X').image_url, '/static/img/default_personaje.jpg')

    def test_post_sin_foto_no_tiene_imagen(self):
        self.assertIsNone(Post(text='x').image_url)