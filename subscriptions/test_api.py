from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, UnidadNarrativa, TemaTransversal
from .models import Suscripcion
from .services import crear_suscripcion


class SuscripcionListCreateAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('lector_sub_api', password='x')
        self.otro_usuario = User.objects.create_user('otro_sub_api', password='x')

        self.obra = Obra.objects.create(titulo='Serie Sub', slug='serie-sub')
        self.unidad = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='arco', nombre='Arco 1', orden_local=1,
        )
        self.tema = TemaTransversal.objects.create(obra=self.obra, nombre='Tema 1')

    def test_requiere_autenticacion_para_listar(self):
        response = self.client.get(reverse('subscriptions_api_list'))
        self.assertEqual(response.status_code, 403)

    def test_lista_solo_las_suscripciones_del_usuario(self):
        crear_suscripcion(self.usuario, self.obra)
        crear_suscripcion(self.otro_usuario, self.obra)

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('subscriptions_api_list'))
        self.assertEqual(len(response.data), 1)

    def test_crear_suscripcion_a_nivel_obra(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(reverse('subscriptions_api_list'), {'obra': self.obra.slug})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['nivel'], 'obra')
        self.assertIsNone(response.data['unidad'])

    def test_crear_suscripcion_a_nivel_unidad(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(reverse('subscriptions_api_list'), {
            'obra': self.obra.slug, 'unidad': self.unidad.id,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['nivel'], 'unidad')
        self.assertEqual(response.data['unidad']['id'], self.unidad.id)

    def test_crear_suscripcion_a_nivel_tema(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(reverse('subscriptions_api_list'), {
            'obra': self.obra.slug, 'tema': self.tema.id,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['nivel'], 'tema')
        self.assertEqual(response.data['tema']['id'], self.tema.id)

    def test_crear_rechaza_unidad_y_tema_simultaneos(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(reverse('subscriptions_api_list'), {
            'obra': self.obra.slug, 'unidad': self.unidad.id, 'tema': self.tema.id,
        })
        self.assertEqual(response.status_code, 400)

    def test_crear_es_idempotente_via_api(self):
        self.client.force_authenticate(user=self.usuario)
        self.client.post(reverse('subscriptions_api_list'), {'obra': self.obra.slug})
        self.client.post(reverse('subscriptions_api_list'), {'obra': self.obra.slug})
        self.assertEqual(Suscripcion.objects.filter(usuario=self.usuario).count(), 1)

    def test_respuesta_incluye_no_leidos(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(reverse('subscriptions_api_list'), {'obra': self.obra.slug})
        self.assertIn('no_leidos', response.data)


class SuscripcionDeleteAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('lector_sub_del', password='x')
        self.otro_usuario = User.objects.create_user('otro_sub_del', password='x')
        self.obra = Obra.objects.create(titulo='Serie Del', slug='serie-del')

    def test_requiere_autenticacion(self):
        suscripcion = crear_suscripcion(self.usuario, self.obra)
        response = self.client.delete(reverse('subscriptions_api_delete', args=[suscripcion.id]))
        self.assertEqual(response.status_code, 403)

    def test_elimina_la_suscripcion_propia(self):
        suscripcion = crear_suscripcion(self.usuario, self.obra)
        self.client.force_authenticate(user=self.usuario)
        response = self.client.delete(reverse('subscriptions_api_delete', args=[suscripcion.id]))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Suscripcion.objects.count(), 0)

    def test_no_permite_eliminar_suscripcion_de_otro_usuario(self):
        suscripcion = crear_suscripcion(self.otro_usuario, self.obra)
        self.client.force_authenticate(user=self.usuario)
        response = self.client.delete(reverse('subscriptions_api_delete', args=[suscripcion.id]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Suscripcion.objects.count(), 1)

    def test_eliminar_suscripcion_inexistente_devuelve_404(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.delete(reverse('subscriptions_api_delete', args=[999999]))
        self.assertEqual(response.status_code, 404)