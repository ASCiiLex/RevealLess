from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, TemaTransversal


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

    def test_agrupa_temas_del_mismo_nombre_entre_obras_relacionadas(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_tema_landing', args=[self.tema_manga.id]))
        self.assertEqual(response.status_code, 200)
        obras_ids = {o['id'] for o in response.data['obras']}
        self.assertEqual(obras_ids, {self.manga.id, self.anime.id})

    def test_no_agrupa_temas_de_obras_no_relacionadas(self):
        otra_obra = Obra.objects.create(titulo='Otra obra', slug='otra-obra')
        TemaTransversal.objects.create(obra=otra_obra, nombre='Frutas del diablo')

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_tema_landing', args=[self.tema_manga.id]))
        obras_ids = {o['id'] for o in response.data['obras']}
        self.assertNotIn(otra_obra.id, obras_ids)