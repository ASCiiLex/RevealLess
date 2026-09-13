from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, UnidadNarrativa, TemaTransversal
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

    def test_progreso_pct_calculado_para_obra_con_progreso(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obras'))
        obra_data = next(
            o for o in response.data['biblioteca'] if o['slug'] == 'con-progreso'
        )
        self.assertEqual(obra_data['progreso_pct'], 100)

    def test_progreso_pct_es_none_sin_progreso_registrado(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obras'))
        obra_data = next(
            o for o in response.data['biblioteca'] if o['slug'] == 'con-suscripcion'
        )
        self.assertIsNone(obra_data['progreso_pct'])

    def test_progreso_pct_es_none_en_descubrir(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obras'))
        obra_data = response.data['descubrir'][0]
        self.assertIsNone(obra_data['progreso_pct'])

    def test_suscrito_true_para_obra_con_suscripcion(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obras'))
        obra_data = next(
            o for o in response.data['biblioteca'] if o['slug'] == 'con-suscripcion'
        )
        self.assertTrue(obra_data['suscrito'])

    def test_suscrito_false_para_obra_solo_con_progreso(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obras'))
        obra_data = next(
            o for o in response.data['biblioteca'] if o['slug'] == 'con-progreso'
        )
        self.assertFalse(obra_data['suscrito'])

    def test_suscripcion_id_presente_para_suscripcion_de_obra_completa(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obras'))
        obra_data = next(
            o for o in response.data['biblioteca'] if o['slug'] == 'con-suscripcion'
        )
        self.assertIsNotNone(obra_data['suscripcion_id'])

    def test_suscripcion_id_es_none_sin_ninguna_suscripcion(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obras'))
        obra_data = next(
            o for o in response.data['biblioteca'] if o['slug'] == 'con-progreso'
        )
        self.assertIsNone(obra_data['suscripcion_id'])

    def test_suscripcion_id_es_none_si_la_suscripcion_es_de_nivel_fino(self):
        """El campo suscripcion_id representa exclusivamente la
        suscripción a nivel obra completa. Si el usuario solo está
        suscrito a una unidad o tema de esa obra, suscrito puede ser
        True (la obra entra en Biblioteca) pero suscripcion_id debe ser
        None, porque no hay ninguna suscripción de obra completa que
        el botón Seguir/Siguiendo del Lomo pueda deshacer."""
        obra_solo_unidad = Obra.objects.create(titulo='Solo unidad', slug='solo-unidad')
        unidad = UnidadNarrativa.objects.create(
            obra=obra_solo_unidad, tipo='arco', nombre='Arco 1', orden_local=1,
        )
        crear_suscripcion(self.usuario, obra_solo_unidad, unidad=unidad)

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obras'))
        obra_data = next(
            o for o in response.data['biblioteca'] if o['slug'] == 'solo-unidad'
        )
        self.assertTrue(obra_data['suscrito'])
        self.assertIsNone(obra_data['suscripcion_id'])

    def test_una_obra_no_aparece_en_ambas_listas(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_obras'))
        slugs_biblioteca = {o['slug'] for o in response.data['biblioteca']}
        slugs_descubrir = {o['slug'] for o in response.data['descubrir']}
        self.assertEqual(slugs_biblioteca & slugs_descubrir, set())


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