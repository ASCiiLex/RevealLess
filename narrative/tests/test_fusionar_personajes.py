from io import StringIO

from django.apps import apps
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from narrative.models import (
    EtapaPersonaje, Obra, Personaje, PropuestaAparicion, RelevanciaPersonaje, UnidadNarrativa,
)
from narrative.services.personajes import fusionar_personajes


class FusionarPersonajesTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo='Obra', slug='obra')
        self.u1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='Uno', orden_local=1)
        self.u2 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='Dos', orden_local=2)
        self.obra.recalcular_orden()
        self.duplicado = Personaje.objects.create(nombre='Arya')
        self.bueno = Personaje.objects.create(nombre='Arya Stark')

    def _propuesta(self, personaje, unidad, estado=PropuestaAparicion.ESTADO_PENDIENTE):
        return PropuestaAparicion.objects.create(
            personaje=personaje, unidad=unidad, origen=PropuestaAparicion.ORIGEN_IA, estado=estado,
        )

    def test_mueve_apariciones_y_propuestas_y_borra_el_duplicado(self):
        self.duplicado.unidades.add(self.u1)
        propuesta = self._propuesta(self.duplicado, self.u2)
        fusionar_personajes(self.duplicado, self.bueno)
        self.assertFalse(Personaje.objects.filter(nombre='Arya').exists())
        self.assertEqual(list(self.bueno.unidades.all()), [self.u1])
        propuesta.refresh_from_db()
        self.assertEqual(propuesta.personaje, self.bueno)

    def test_misma_unidad_deja_una_y_prevalece_la_aprobada(self):
        self._propuesta(self.duplicado, self.u1, PropuestaAparicion.ESTADO_APROBADA)
        self._propuesta(self.bueno, self.u1)
        fusionar_personajes(self.duplicado, self.bueno)
        propuestas = PropuestaAparicion.objects.filter(personaje=self.bueno)
        self.assertEqual(propuestas.count(), 1)
        self.assertEqual(propuestas.get().estado, PropuestaAparicion.ESTADO_APROBADA)

    def test_hereda_wikidata_si_el_destino_no_tiene(self):
        self.duplicado.wikidata_id = 'Q1'
        self.duplicado.save()
        fusionar_personajes(self.duplicado, self.bueno)
        self.bueno.refresh_from_db()
        self.assertEqual(self.bueno.wikidata_id, 'Q1')

    def test_mueve_etapas(self):
        EtapaPersonaje.objects.create(personaje=self.duplicado, visible_tras=self.u1, nota='Dato')
        fusionar_personajes(self.duplicado, self.bueno)
        self.assertEqual(self.bueno.etapas.get().nota, 'Dato')

    def test_relevancia_misma_obra_conserva_la_mayor(self):
        RelevanciaPersonaje.objects.create(
            personaje=self.duplicado, obra=self.obra, nivel=RelevanciaPersonaje.NIVEL_PROTAGONISTA,
        )
        RelevanciaPersonaje.objects.create(
            personaje=self.bueno, obra=self.obra, nivel=RelevanciaPersonaje.NIVEL_SECUNDARIO,
        )
        fusionar_personajes(self.duplicado, self.bueno)
        self.assertEqual(self.bueno.relevancias.get().nivel, RelevanciaPersonaje.NIVEL_PROTAGONISTA)

    def test_suscripciones_sin_duplicar_por_usuario(self):
        Suscripcion = apps.get_model('subscriptions', 'Suscripcion')
        ambos = User.objects.create_user('ambos', password='x')
        solo_dup = User.objects.create_user('solo', password='x')
        Suscripcion.objects.create(usuario=ambos, personaje=self.duplicado)
        Suscripcion.objects.create(usuario=ambos, personaje=self.bueno)
        Suscripcion.objects.create(usuario=solo_dup, personaje=self.duplicado)
        fusionar_personajes(self.duplicado, self.bueno)
        self.assertEqual(Suscripcion.objects.filter(personaje=self.bueno, usuario=ambos).count(), 1)
        self.assertTrue(Suscripcion.objects.filter(personaje=self.bueno, usuario=solo_dup).exists())

    def test_no_se_fusiona_consigo_mismo(self):
        with self.assertRaises(ValueError):
            fusionar_personajes(self.bueno, self.bueno)

    def test_comando_en_simulacion_no_guarda(self):
        call_command(
            'fusionar_personajes', str(self.duplicado.pk), destino=self.bueno.pk, dry_run=True, stdout=StringIO(),
        )
        self.assertTrue(Personaje.objects.filter(pk=self.duplicado.pk).exists())