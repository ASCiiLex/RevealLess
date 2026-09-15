from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, UnidadNarrativa, TemaTransversal
from narrative.services import actualizar_progreso
from subscriptions.services import crear_suscripcion


class ObraLandingAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('landing_user', password='x')
        self.otro_usuario = User.objects.create_user('landing_otro', password='x')

        self.obra = Obra.objects.create(
            titulo='Serie Landing', slug='serie-landing', sinopsis='Una sinopsis de prueba',
        )
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()

        self.tema = TemaTransversal.objects.create(obra=self.obra, nombre='Tema Landing')

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        self.assertEqual(response.status_code, 403)

    def test_devuelve_404_si_la_obra_no_existe(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=['no-existe']))
        self.assertEqual(response.status_code, 404)

    def test_incluye_sinopsis(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        self.assertEqual(response.data['sinopsis'], 'Una sinopsis de prueba')

    def test_progreso_pct_none_sin_progreso(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        self.assertIsNone(response.data['progreso_pct'])

    def test_progreso_pct_calculado_con_progreso(self):
        actualizar_progreso(self.usuario, self.obra, self.e2)
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        self.assertEqual(response.data['progreso_pct'], 100)

    def test_total_suscriptores_cuenta_usuarios_distintos(self):
        crear_suscripcion(self.usuario, self.obra)
        crear_suscripcion(self.otro_usuario, self.obra, tema=self.tema)

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        self.assertEqual(response.data['total_suscriptores'], 2)

    def test_incluye_temas_con_estado_de_suscripcion(self):
        crear_suscripcion(self.usuario, self.obra, tema=self.tema)

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        tema_data = response.data['temas'][0]
        self.assertEqual(tema_data['nombre'], 'Tema Landing')
        self.assertTrue(tema_data['suscrito'])
        self.assertIsNotNone(tema_data['suscripcion_id'])

    def test_suscrito_false_sin_suscripcion_de_obra(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug]))
        self.assertFalse(response.data['suscrito'])