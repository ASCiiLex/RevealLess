from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from ..models import Obra, TemaTransversal, SolicitudTema
from ..services import aprobar_solicitud_tema, rechazar_solicitud_tema


class SolicitudTemaListCreateAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('proponente', password='x')
        self.otro_usuario = User.objects.create_user('otro_proponente', password='x')
        self.obra = Obra.objects.create(titulo='Serie Solicitud', slug='serie-solicitud')

    def test_requiere_autenticacion_para_listar(self):
        response = self.client.get(reverse('narrative_api_solicitudes_tema'))
        self.assertEqual(response.status_code, 403)

    def test_crear_solicitud_queda_pendiente(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(reverse('narrative_api_solicitudes_tema'), {
            'obra': self.obra.id, 'nombre': 'Las recetas de Sanji',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['estado'], 'pendiente')

    def test_crear_solicitud_no_crea_tema_directamente(self):
        self.client.force_authenticate(user=self.usuario)
        self.client.post(reverse('narrative_api_solicitudes_tema'), {
            'obra': self.obra.id, 'nombre': 'Las recetas de Sanji',
        })
        self.assertEqual(TemaTransversal.objects.count(), 0)

    def test_lista_solo_las_solicitudes_del_usuario(self):
        SolicitudTema.objects.create(obra=self.obra, usuario=self.usuario, nombre='Tema propio')
        SolicitudTema.objects.create(obra=self.obra, usuario=self.otro_usuario, nombre='Tema ajeno')

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_solicitudes_tema'))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Tema propio')


class AprobarSolicitudTemaTests(TestCase):
    """Lógica pura de services.py, sin Django admin ni HttpRequest de por
    medio — message_user() es responsabilidad exclusiva del admin y no
    necesita montar el framework de mensajes para verificar los efectos
    reales en base de datos."""

    def setUp(self):
        self.usuario = User.objects.create_user('proponente_admin', password='x')
        self.obra = Obra.objects.create(titulo='Serie Admin', slug='serie-admin')

    def test_aprobar_crea_el_tema_transversal(self):
        solicitud = SolicitudTema.objects.create(
            obra=self.obra, usuario=self.usuario, nombre='Frutas del diablo',
        )

        tema = aprobar_solicitud_tema(solicitud)

        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudTema.ESTADO_APROBADA)
        self.assertIsNotNone(solicitud.resuelto_en)
        self.assertIsNotNone(tema)
        self.assertTrue(
            TemaTransversal.objects.filter(obra=self.obra, nombre='Frutas del diablo').exists()
        )

    def test_aprobar_no_duplica_tema_si_ya_existe(self):
        TemaTransversal.objects.create(obra=self.obra, nombre='Ya existe')
        solicitud = SolicitudTema.objects.create(
            obra=self.obra, usuario=self.usuario, nombre='Ya existe',
        )

        aprobar_solicitud_tema(solicitud)

        self.assertEqual(
            TemaTransversal.objects.filter(obra=self.obra, nombre='Ya existe').count(), 1
        )

    def test_aprobar_ignora_solicitudes_ya_resueltas(self):
        solicitud = SolicitudTema.objects.create(
            obra=self.obra, usuario=self.usuario, nombre='Tema rechazado',
            estado=SolicitudTema.ESTADO_RECHAZADA,
        )

        resultado = aprobar_solicitud_tema(solicitud)

        solicitud.refresh_from_db()
        self.assertIsNone(resultado)
        self.assertEqual(solicitud.estado, SolicitudTema.ESTADO_RECHAZADA)
        self.assertFalse(TemaTransversal.objects.filter(nombre='Tema rechazado').exists())

    def test_rechazar_no_crea_tema(self):
        solicitud = SolicitudTema.objects.create(
            obra=self.obra, usuario=self.usuario, nombre='Tema a rechazar',
        )

        resultado = rechazar_solicitud_tema(solicitud)

        solicitud.refresh_from_db()
        self.assertTrue(resultado)
        self.assertEqual(solicitud.estado, SolicitudTema.ESTADO_RECHAZADA)
        self.assertFalse(TemaTransversal.objects.filter(nombre='Tema a rechazar').exists())

    def test_rechazar_ignora_solicitudes_ya_resueltas(self):
        solicitud = SolicitudTema.objects.create(
            obra=self.obra, usuario=self.usuario, nombre='Tema ya aprobado',
            estado=SolicitudTema.ESTADO_APROBADA,
        )

        resultado = rechazar_solicitud_tema(solicitud)

        solicitud.refresh_from_db()
        self.assertFalse(resultado)
        self.assertEqual(solicitud.estado, SolicitudTema.ESTADO_APROBADA)