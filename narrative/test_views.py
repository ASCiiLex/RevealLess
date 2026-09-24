from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Obra


class ObraReactViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('react_user', password='x')
        self.obra = Obra.objects.create(titulo='Serie React', slug='serie-react')
        self.client.force_login(self.user)

    def test_progreso_react_devuelve_404_si_obra_no_existe(self):
        url = reverse('narrative_progreso_react', kwargs={'obra_slug': 'no-existe'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_progreso_react_ok_si_obra_existe(self):
        url = reverse('narrative_progreso_react', kwargs={'obra_slug': self.obra.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_obra_landing_react_devuelve_404_si_obra_no_existe(self):
        url = reverse('narrative_obra_landing_react', kwargs={'obra_slug': 'no-existe'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_obra_temas_react_devuelve_404_si_obra_no_existe(self):
        url = reverse('narrative_obra_temas_react', kwargs={'obra_slug': 'no-existe'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)