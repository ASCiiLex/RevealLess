from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from ..models import Obra, UnidadNarrativa
from ..services import actualizar_progreso


class ProgresoAPIValidacionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        usuario = User.objects.create_user('validacion_progreso', password='x')
        obra = Obra.objects.create(titulo='Serie Validacion', slug='serie-validacion')
        self.episodios = [
            UnidadNarrativa.objects.create(obra=obra, tipo='episodio', nombre=f'E{i}', orden_local=i)
            for i in range(1, 8)
        ]
        obra.recalcular_orden()
        for e in self.episodios:
            e.refresh_from_db()

        actualizar_progreso(usuario, obra, self.episodios[0])
        self.client.force_authenticate(user=usuario)
        self.url = reverse('narrative_api_progreso', args=[obra.slug])

    def _declarar(self, unidad_actual, **extra):
        return self.client.post(self.url, {'unidad_actual': unidad_actual, **extra})

    def test_confirmado_false_como_texto_no_salta_la_confirmacion(self):
        """Regresión: bool('false') era True y se saltaba la confirmación de salto grande."""
        response = self._declarar(self.episodios[-1].id, confirmado='false')
        self.assertEqual(response.status_code, 409)

    def test_confirmado_true_como_texto_aplica_el_salto(self):
        self.assertEqual(self._declarar(self.episodios[-1].id, confirmado='true').status_code, 200)

    def test_unidad_actual_no_numerica_devuelve_400(self):
        self.assertEqual(self._declarar('abc').status_code, 400)


class FeedAPIValidacionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=User.objects.create_user('validacion_feed', password='x'))
        self.url = reverse('narrative_api_feed')

    def test_obra_no_numerica_devuelve_400(self):
        self.assertEqual(self.client.get(self.url, {'obra': 'abc'}).status_code, 400)

    def test_tema_no_numerico_devuelve_400(self):
        self.assertEqual(self.client.get(self.url, {'tema': 'abc'}).status_code, 400)