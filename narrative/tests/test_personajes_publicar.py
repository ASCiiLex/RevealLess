from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, Personaje, UnidadNarrativa
from narrative.services import actualizar_progreso


class PersonajesPublicarAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('comparador', password='x')
        self.obra = Obra.objects.create(titulo='Serie', slug='serie-comparar')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.e2 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E2', orden_local=2)
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()
        Personaje.objects.create(nombre='Luffy').unidades.add(self.e1)
        Personaje.objects.create(nombre='Kuro').unidades.add(self.e2)
        self.url = reverse('narrative_api_personajes_publicar', args=[self.obra.slug])
        self.client.force_authenticate(user=self.usuario)

    def _nombres(self, **params):
        return [p['nombre'] for p in self.client.get(self.url, params).data['personajes']]

    def test_sin_progreso_no_ofrece_personajes(self):
        self.assertEqual(self._nombres(), [])

    def test_solo_personajes_ya_aparecidos(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.assertEqual(self._nombres(), ['Luffy'])

    def test_filtra_por_texto(self):
        actualizar_progreso(self.usuario, self.obra, self.e2)
        self.assertEqual(self._nombres(q='ku'), ['Kuro'])