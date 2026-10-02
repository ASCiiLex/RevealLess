from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from narrative.models import EtapaPersonaje, Personaje
from narrative.services import actualizar_progreso
from posts.tests.utils import crear_obra


class PersonajeLandingContextoTests(TestCase):
    """El mismo personaje va por delante en el manga que en el anime."""

    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('lector_ctx', password='x')
        self.client.force_authenticate(user=self.usuario)
        self.anime, ua = crear_obra('anime-ctx', 2)
        self.manga, um = crear_obra('manga-ctx', 2)
        robin = Personaje.objects.create(nombre='Miss All Sunday')
        robin.unidades.add(ua[0], um[0])
        EtapaPersonaje.objects.create(personaje=robin, visible_tras=um[1], alias='Nico Robin')
        actualizar_progreso(self.usuario, self.anime, ua[0])
        actualizar_progreso(self.usuario, self.manga, um[1])
        self.url = f'/narrative/api/personajes/{robin.id}/'

    def test_sin_obra_junta_todas_las_obras_alcanzadas(self):
        datos = self.client.get(self.url).data
        self.assertEqual(datos['nombre'], 'Nico Robin')
        self.assertIsNone(datos['contexto'])

    def test_con_obra_muestra_el_estado_de_esa_obra(self):
        datos = self.client.get(self.url, {'obra': 'anime-ctx'}).data
        self.assertEqual(datos['nombre'], 'Miss All Sunday')
        self.assertEqual(datos['contexto']['slug'], 'anime-ctx')

    def test_obra_no_alcanzada_se_ignora(self):
        crear_obra('otra-ctx', 1)
        datos = self.client.get(self.url, {'obra': 'otra-ctx'}).data
        self.assertEqual(datos['nombre'], 'Nico Robin')
        self.assertIsNone(datos['contexto'])