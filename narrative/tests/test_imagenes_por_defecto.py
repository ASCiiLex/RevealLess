from django.test import SimpleTestCase

from narrative.models import Obra, Personaje


class ImagenPorDefectoTests(SimpleTestCase):
    def test_obra_sin_imagen_usa_la_portada_de_su_tipo(self):
        casos = {
            Obra.TIPO_PELICULA: '/static/img/default_pelicula.jpg',
            Obra.TIPO_MANGA: '/static/img/default_manga.jpg',
            Obra.TIPO_LIBRO: '/static/img/default_libro.jpg',
            Obra.TIPO_SERIE: '/static/img/default_serie.jpg',
            Obra.TIPO_OVA: '/static/img/default_serie.jpg',
        }
        for tipo, esperado in casos.items():
            with self.subTest(tipo=tipo):
                self.assertEqual(Obra(tipo=tipo).image_url, esperado)

    def test_personaje_sin_imagen_usa_su_portada_propia(self):
        self.assertEqual(Personaje(nombre='X').image_url, '/static/img/default_personaje.jpg')