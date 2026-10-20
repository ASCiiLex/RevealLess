from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from notifications.models import Notification
from narrative.models import Obra, SolicitudObra, UnidadNarrativa
from narrative.services.solicitudes_obra import (
    MAX_PENDIENTES_POR_USUARIO,
    aprobar_solicitud_obra,
    rechazar_solicitud_obra,
)

URL = 'narrative_api_solicitudes_obra'


class ProponerObraTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('sugiere_obra', password='x')
        self.client.force_authenticate(user=self.usuario)

    def _proponer(self, **datos):
        return self.client.post(reverse(URL), {'titulo': 'Dune', 'tipo': 'pelicula', **datos})

    def test_requiere_autenticacion(self):
        self.assertEqual(APIClient().get(reverse(URL)).status_code, 403)

    def test_crea_la_solicitud_pendiente_sin_crear_la_obra(self):
        response = self._proponer(enlace='https://www.imdb.com/title/tt1160419/')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['estado'], SolicitudObra.ESTADO_PENDIENTE)
        self.assertFalse(Obra.objects.exists())

    def test_obra_ya_en_el_catalogo_devuelve_400(self):
        Obra.objects.create(titulo='Dune', slug='dune')
        self.assertEqual(self._proponer().status_code, 400)

    def test_no_duplica_la_misma_sugerencia_pendiente(self):
        self._proponer()
        self.assertEqual(self._proponer(titulo='dune').status_code, 400)
        self.assertEqual(SolicitudObra.objects.count(), 1)

    def test_limite_de_sugerencias_pendientes(self):
        for i in range(MAX_PENDIENTES_POR_USUARIO):
            SolicitudObra.objects.create(usuario=self.usuario, titulo=f'Obra {i}')
        self.assertEqual(self._proponer().status_code, 400)

    def test_lista_solo_las_propias(self):
        otro = User.objects.create_user('otro_sugiere', password='x')
        SolicitudObra.objects.create(usuario=otro, titulo='Ajena')
        self._proponer()
        self.assertEqual([s['titulo'] for s in self.client.get(reverse(URL)).data], ['Dune'])


class ResolverSolicitudObraTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin_catalogo', password='x')
        ana = User.objects.create_user('ana_sugiere', password='x')
        luis = User.objects.create_user('luis_sugiere', password='x')
        self.s1 = SolicitudObra.objects.create(usuario=ana, titulo='Dune', tipo=Obra.TIPO_PELICULA)
        self.s2 = SolicitudObra.objects.create(usuario=luis, titulo='dune', tipo=Obra.TIPO_PELICULA)

    def _estados(self):
        return {s.estado for s in SolicitudObra.objects.all()}

    def test_aprobar_crea_la_obra_con_previo_y_resuelve_y_avisa_a_todos(self):
        obra = aprobar_solicitud_obra(self.s1, self.admin)

        self.assertEqual((obra.titulo, obra.tipo), ('Dune', Obra.TIPO_PELICULA))
        self.assertTrue(obra.unidades.filter(tipo=UnidadNarrativa.TIPO_PREVIO).exists())
        self.assertEqual(self._estados(), {SolicitudObra.ESTADO_APROBADA})
        self.assertEqual(Notification.objects.filter(target_type='obra', target_id=obra.id).count(), 2)
        self.assertEqual(Notification.objects.first().url, f'/narrative/obra/{obra.slug}/')

    def test_aprobar_con_obra_vinculada_no_crea_otra(self):
        existente = Obra.objects.create(titulo='Dune (Película)', slug='dune-pelicula')
        self.s1.obra = existente
        self.s1.save()

        self.assertEqual(aprobar_solicitud_obra(self.s1, self.admin), existente)
        self.assertEqual(Obra.objects.count(), 1)

    def test_aprobar_busca_un_slug_libre(self):
        Obra.objects.create(titulo='Otra obra', slug='dune')
        self.assertEqual(aprobar_solicitud_obra(self.s1, self.admin).slug, 'dune-2')

    def test_rechazar_resuelve_avisa_y_no_crea_nada(self):
        self.assertTrue(rechazar_solicitud_obra(self.s1, self.admin))
        self.assertEqual(self._estados(), {SolicitudObra.ESTADO_RECHAZADA})
        self.assertFalse(Obra.objects.exists())
        self.assertEqual(Notification.objects.filter(target_type='obra', target_id=None).count(), 2)

    def test_ignora_solicitudes_ya_resueltas(self):
        self.s1.estado = SolicitudObra.ESTADO_APROBADA
        self.s1.save()
        self.assertIsNone(aprobar_solicitud_obra(self.s1, self.admin))
        self.assertFalse(rechazar_solicitud_obra(self.s1, self.admin))