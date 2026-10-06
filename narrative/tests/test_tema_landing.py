from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Categoria, Obra, TemaTransversal


class TemaLandingAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('lector', password='x')
        self.manga = Obra.objects.create(titulo='One Piece Manga', slug='one-piece-manga')
        self.anime = Obra.objects.create(
            titulo='One Piece Anime', slug='one-piece-anime', adapta_a=self.manga,
        )
        self.tema_manga = TemaTransversal.objects.create(obra=self.manga, nombre='Frutas del diablo')
        self.tema_anime = TemaTransversal.objects.create(obra=self.anime, nombre='Frutas del diablo')

    def _obras_ids(self, tema):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_tema_landing', args=[tema.id]))
        self.assertEqual(response.status_code, 200)
        return {o['id'] for o in response.data['obras']}

    def test_agrupa_temas_del_mismo_nombre_entre_obras_relacionadas(self):
        self.assertEqual(self._obras_ids(self.tema_manga), {self.manga.id, self.anime.id})

    def test_no_agrupa_temas_de_obras_no_relacionadas(self):
        otra_obra = Obra.objects.create(titulo='Otra obra', slug='otra-obra')
        TemaTransversal.objects.create(obra=otra_obra, nombre='Frutas del diablo')
        self.assertNotIn(otra_obra.id, self._obras_ids(self.tema_manga))

    def test_agrupa_temas_dentro_del_mismo_universo(self):
        universo = Categoria.objects.create(nombre='One Piece', es_universo=True)
        live_action = Obra.objects.create(titulo='One Piece (Netflix)', slug='one-piece-netflix')
        live_action.categorias.add(universo)
        self.manga.categorias.add(universo)
        TemaTransversal.objects.create(obra=live_action, nombre='Frutas del diablo')
        self.assertIn(live_action.id, self._obras_ids(self.tema_manga))