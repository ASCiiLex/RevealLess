from django.contrib.auth.models import User
from django.test import TestCase

from narrative.models import Obra

URL = '/narrative/api/buscar/'


class BusquedaObrasTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user('buscador', password='x'))

    def _slugs(self, q):
        response = self.client.get(URL, {'q': q})
        self.assertEqual(response.status_code, 200)
        return [o['slug'] for o in response.json()['obras']]

    def test_encuentra_por_slug_aunque_el_titulo_no_tenga_espacio(self):
        Obra.objects.create(titulo='StarWars: Películas', slug='star-wars-peliculas')
        self.assertIn('star-wars-peliculas', self._slugs('star wars'))

    def test_busqueda_sin_tilde_encuentra_titulo_con_tilde(self):
        Obra.objects.create(titulo='Star Wars: Películas', slug='star-wars-peliculas')
        self.assertIn('star-wars-peliculas', self._slugs('peliculas'))

    def test_devuelve_hasta_diez_obras(self):
        for i in range(12):
            Obra.objects.create(titulo=f'Star Wars {i:02d}', slug=f'star-wars-{i}')
        self.assertEqual(len(self._slugs('star wars')), 10)

    def test_prioriza_titulos_que_empiezan_por_la_busqueda(self):
        Obra.objects.create(titulo='Anime de Naruto', slug='anime-de-naruto')
        Obra.objects.create(titulo='Naruto', slug='naruto')
        self.assertEqual(self._slugs('naruto')[0], 'naruto')