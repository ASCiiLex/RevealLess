from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra, Personaje, ProgresoUsuario, PropuestaAparicion, UnidadNarrativa
from narrative.services.personajes import (
    aplicar_cambio_propuesta, aprobar_propuesta, eliminar_propuesta, rechazar_propuesta,
)

APROBADA = PropuestaAparicion.ESTADO_APROBADA
PENDIENTE = PropuestaAparicion.ESTADO_PENDIENTE


class PropuestaAparicionTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('lectora', password='x')
        self.client.force_login(self.usuario)
        self.obra = Obra.objects.create(titulo='Obra', slug='obra')
        self.u1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='Uno', orden_local=1)
        self.u2 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='Dos', orden_local=2)
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

    def _cambiar(self, **campos):
        # Simula la edición en el admin: guarda y sincroniza con los valores previos.
        previo = (self.propuesta.estado, self.propuesta.unidad_id)
        for campo, valor in campos.items():
            setattr(self.propuesta, campo, valor)
        self.propuesta.save()
        aplicar_cambio_propuesta(self.propuesta, *previo)

    def test_una_propuesta_pendiente_no_se_muestra(self):
        self.assertEqual(self._nombres_en_landing(), [])

    def test_aprobar_la_hace_visible(self):
        aprobar_propuesta(self.propuesta)
        self.propuesta.refresh_from_db()
        self.assertEqual(self.propuesta.estado, APROBADA)
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

    def test_aprobar_a_mano_cambiando_el_estado(self):
        self._cambiar(estado=APROBADA)
        self.propuesta.refresh_from_db()
        self.assertIsNotNone(self.propuesta.resuelto_en)
        self.assertEqual(self._nombres_en_landing(), ['Heroína'])

    def test_volver_a_pendiente_retira_la_aparicion(self):
        aprobar_propuesta(self.propuesta)
        self._cambiar(estado=PENDIENTE)
        self.propuesta.refresh_from_db()
        self.assertIsNone(self.propuesta.resuelto_en)
        self.assertFalse(self.personaje.unidades.exists())

    def test_mover_una_aprobada_cambia_la_aparicion(self):
        aprobar_propuesta(self.propuesta)
        self._cambiar(unidad=self.u2)
        self.assertEqual(list(self.personaje.unidades.all()), [self.u2])

    def test_mover_una_pendiente_no_toca_apariciones(self):
        self._cambiar(unidad=self.u2)
        self.assertFalse(self.personaje.unidades.exists())

    def test_aparicion_manual_nueva_aprobada(self):
        manual = PropuestaAparicion.objects.create(personaje=self.personaje, unidad=self.u2, estado=APROBADA)
        aplicar_cambio_propuesta(manual)
        self.assertEqual(manual.origen, PropuestaAparicion.ORIGEN_MANUAL)
        self.assertIn(self.u2, self.personaje.unidades.all())

    def test_eliminar_una_aprobada_retira_la_aparicion(self):
        aprobar_propuesta(self.propuesta)
        eliminar_propuesta(self.propuesta)
        self.assertFalse(self.personaje.unidades.exists())
        self.assertFalse(PropuestaAparicion.objects.exists())