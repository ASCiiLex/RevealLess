from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, UnidadNarrativa
from narrative.services import actualizar_progreso
from subscriptions.services import crear_suscripcion


class CatalogoObrasAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('lector_catalogo', password='x')

        self.obra_con_progreso = Obra.objects.create(titulo='Con progreso', slug='con-progreso')
        self.obra_con_suscripcion = Obra.objects.create(titulo='Con suscripcion', slug='con-suscripcion')
        self.obra_sin_relacion = Obra.objects.create(titulo='Sin relacion', slug='sin-relacion')

        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra_con_progreso, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra_con_progreso.recalcular_orden()
        self.e1.refresh_from_db()

        actualizar_progreso(self.usuario, self.obra_con_progreso, self.e1)
        crear_suscripcion(self.usuario, self.obra_con_suscripcion)

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('narrative_api_obras'))
        self.assertEqual(response.status_code, 403)

    def test_obra_con_progreso_va_a_biblioteca(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obras'))
        slugs = [o['slug'] for o in response.data['biblioteca']]
        self.assertIn('con-progreso', slugs)

    def test_obra_con_suscripcion_va_a_biblioteca(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obras'))
        slugs = [o['slug'] for o in response.data['biblioteca']]
        self.assertIn('con-suscripcion', slugs)

    def test_obra_sin_relacion_va_a_descubrir(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obras'))
        slugs_descubrir = [o['slug'] for o in response.data['descubrir']]
        slugs_biblioteca = [o['slug'] for o in response.data['biblioteca']]
        self.assertIn('sin-relacion', slugs_descubrir)
        self.assertNotIn('sin-relacion', slugs_biblioteca)

    def test_una_obra_no_aparece_en_ambas_listas(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obras'))
        slugs_biblioteca = {o['slug'] for o in response.data['biblioteca']}
        slugs_descubrir = {o['slug'] for o in response.data['descubrir']}
        self.assertEqual(slugs_biblioteca & slugs_descubrir, set())

    def test_respuesta_incluye_imagen_url_y_categorias(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obras'))
        obra_data = response.data['biblioteca'][0]
        self.assertIn('imagen_url', obra_data)
        self.assertIn('categorias', obra_data)