from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, TemaTransversal, UnidadNarrativa
from narrative.services import actualizar_progreso
from subscriptions.models import Suscripcion


class ObrasPublicarAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('autora', password='x')
        self.url = reverse('narrative_api_obras_publicar')

        self.con_progreso = Obra.objects.create(titulo='Con progreso', slug='con-progreso')
        unidad = UnidadNarrativa.objects.create(
            obra=self.con_progreso, tipo='episodio', nombre='Uno', orden_local=1,
        )
        self.con_progreso.recalcular_orden()
        unidad.refresh_from_db()
        actualizar_progreso(self.usuario, self.con_progreso, unidad)

        self.seguida = Obra.objects.create(titulo='Seguida', slug='seguida')
        Suscripcion.objects.create(usuario=self.usuario, obra=self.seguida)

        self.ajena = Obra.objects.create(titulo='Ajena', slug='ajena')

    def _get(self):
        self.client.force_authenticate(user=self.usuario)
        return self.client.get(self.url)

    def test_requiere_autenticacion(self):
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_solo_obras_de_la_biblioteca(self):
        response = self._get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual([o['slug'] for o in response.data['obras']], ['con-progreso', 'seguida'])

    def test_incluye_obras_silenciadas(self):
        silenciada = Obra.objects.create(titulo='Silenciada', slug='silenciada')
        Suscripcion.objects.create(usuario=self.usuario, obra=silenciada, activa=False)
        self.assertIn('silenciada', [o['slug'] for o in self._get().data['obras']])

    def test_temas_solo_de_obras_de_la_biblioteca(self):
        TemaTransversal.objects.create(obra=self.seguida, nombre='Propio')
        TemaTransversal.objects.create(obra=self.ajena, nombre='Ajeno')
        temas = self._get().data['temas']
        self.assertEqual([(t['nombre'], t['obra_slug']) for t in temas], [('Propio', 'seguida')])

    def test_sin_biblioteca_devuelve_listas_vacias(self):
        otro = User.objects.create_user('nuevo', password='x')
        self.client.force_authenticate(user=otro)
        self.assertEqual(self.client.get(self.url).data, {'obras': [], 'temas': []})