from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, UnidadNarrativa, TemaTransversal


class ObraDetalleAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('lector_detalle', password='x')
        self.obra = Obra.objects.create(titulo='Serie Detalle', slug='serie-detalle')
        self.unidad = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='arco', nombre='Arco 1', orden_local=1,
        )
        self.tema = TemaTransversal.objects.create(obra=self.obra, nombre='Tema 1')

    def test_requiere_autenticacion(self):
        response = self.client.get(
            reverse('narrative_api_obra_detalle', args=[self.obra.slug])
        )
        self.assertEqual(response.status_code, 403)

    def test_devuelve_404_si_la_obra_no_existe(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(
            reverse('narrative_api_obra_detalle', args=['no-existe'])
        )
        self.assertEqual(response.status_code, 404)

    def test_incluye_unidades_y_temas_de_la_obra(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(
            reverse('narrative_api_obra_detalle', args=[self.obra.slug])
        )
        unidad_ids = [u['id'] for u in response.data['unidades']]
        tema_nombres = [t['nombre'] for t in response.data['temas']]
        self.assertIn(self.unidad.id, unidad_ids)
        self.assertIn('Tema 1', tema_nombres)

    def test_no_requiere_progreso_previo_del_usuario(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(
            reverse('narrative_api_obra_detalle', args=[self.obra.slug])
        )
        self.assertEqual(response.status_code, 200)