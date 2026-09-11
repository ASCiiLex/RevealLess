from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Obra, TemaTransversal


class BuscarAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('buscador', password='x')
        self.obra = Obra.objects.create(titulo='One Piece', slug='one-piece')
        self.otra_obra = Obra.objects.create(titulo='Naruto', slug='naruto')
        self.tema = TemaTransversal.objects.create(obra=self.obra, nombre='Frutas del diablo')

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'one'})
        self.assertEqual(response.status_code, 403)

    def test_busca_obras_por_titulo_parcial(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'one'})
        titulos = [o['titulo'] for o in response.data['obras']]
        self.assertIn('One Piece', titulos)
        self.assertNotIn('Naruto', titulos)

    def test_busca_temas_por_nombre_parcial(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'fruta'})
        nombres = [t['nombre'] for t in response.data['temas']]
        self.assertIn('Frutas del diablo', nombres)

    def test_tema_incluye_datos_de_su_obra(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'fruta'})
        tema_data = response.data['temas'][0]
        self.assertEqual(tema_data['obra_slug'], 'one-piece')
        self.assertEqual(tema_data['obra_titulo'], 'One Piece')

    def test_busqueda_case_insensitive(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'ONE'})
        titulos = [o['titulo'] for o in response.data['obras']]
        self.assertIn('One Piece', titulos)

    def test_query_corta_devuelve_listas_vacias(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'o'})
        self.assertEqual(response.data['obras'], [])
        self.assertEqual(response.data['temas'], [])

    def test_sin_query_devuelve_listas_vacias(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'))
        self.assertEqual(response.data['obras'], [])
        self.assertEqual(response.data['temas'], [])

    def test_query_sin_coincidencias_devuelve_listas_vacias(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'inexistente'})
        self.assertEqual(response.data['obras'], [])
        self.assertEqual(response.data['temas'], [])