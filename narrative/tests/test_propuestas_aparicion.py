from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra, Personaje, ProgresoUsuario, PropuestaAparicion, UnidadNarrativa
from narrative.services.personajes import aprobar_propuesta, rechazar_propuesta


class PropuestaAparicionTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('lectora', password='x')
        self.client.force_login(self.usuario)
        self.obra = Obra.objects.create(titulo='Obra', slug='obra')
        self.u1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='Uno', orden_local=1)
        self.obra.recalcular_orden()
        self.u1.refresh_from_db()
        ProgresoUsuario.objects.create(
            usuario=self.usuario, obra=self.obra, unidad_actual=self.u1, orden_absoluto=self.u1.orden_fin,
        )
        self.personaje = Personaje.objects.create(nombre='Heroína')
        self.propuesta = PropuestaAparicion.objects.create(
            personaje=self.personaje, unidad=self.u1, origen=PropuestaAparicion.ORIGEN_IA, confianza=0.9,
        )

    def _nombres_en_landing(self):
        datos = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug])).json()
        return [p['nombre'] for p in datos['personajes']]

    def test_una_propuesta_pendiente_no_se_muestra(self):
        self.assertEqual(self._nombres_en_landing(), [])

    def test_aprobar_la_hace_visible(self):
        aprobar_propuesta(self.propuesta)
        self.propuesta.refresh_from_db()
        self.assertEqual(self.propuesta.estado, PropuestaAparicion.ESTADO_APROBADA)
        self.assertIsNotNone(self.propuesta.resuelto_en)
        self.assertEqual(self._nombres_en_landing(), ['Heroína'])

    def test_rechazar_una_aprobada_la_retira(self):
        aprobar_propuesta(self.propuesta)
        rechazar_propuesta(self.propuesta)
        self.assertEqual(self._nombres_en_landing(), [])
        self.assertFalse(self.personaje.unidades.exists())

    def test_no_duplica_la_misma_aparicion(self):
        with transaction.atomic(), self.assertRaises(IntegrityError):
            PropuestaAparicion.objects.create(
                personaje=self.personaje, unidad=self.u1, origen=PropuestaAparicion.ORIGEN_WIKIDATA,
            )