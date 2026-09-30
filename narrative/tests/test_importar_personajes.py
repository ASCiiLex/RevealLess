import datetime
import os
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from narrative.models import ExternalId, Obra, Personaje, PropuestaAparicion, UnidadNarrativa

MODULO = 'narrative.management.commands.importar_personajes'


class ImportarPersonajesTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo='Saga', slug='saga', tipo=Obra.TIPO_PELICULA)
        self.u1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='pelicula', nombre='Primera', orden_local=1, fecha=datetime.date(2008, 5, 2),
        )
        self.u2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='pelicula', nombre='Segunda', orden_local=2, fecha=datetime.date(2010, 5, 7),
        )
        self.obra.recalcular_orden()
        self.u1.refresh_from_db()
        self.u2.refresh_from_db()
        ExternalId.objects.create(source=ExternalId.SOURCE_WIKIDATA, external_id='Q1', obra=self.obra)

        self.partes = [
            {
                'qid': 'Q10', 'titulo': 'First', 'fechas': [datetime.date(2008, 4, 30)], 'clase': 'pelicula',
                'personajes': [{'qid': 'Q100', 'nombre': 'Heroína'}],
            },
            {
                # Episodio de otra serie con la misma fecha: se descarta en una obra de películas.
                'qid': 'Q11', 'titulo': 'Episodio', 'fechas': [datetime.date(2010, 5, 7)], 'clase': 'tv',
                'personajes': [{'qid': 'Q300', 'nombre': 'Ajeno'}],
            },
        ]
        self.de_obra = [{'qid': 'Q100', 'nombre': 'Heroína'}, {'qid': 'Q200', 'nombre': 'Villano'}]

    def _importar(self, propuestas, nuevos=(), **opciones):
        with patch(f'{MODULO}.wikidata.partes_de_obra', return_value=self.partes), \
                patch(f'{MODULO}.wikidata.personajes_de_obra', return_value=self.de_obra), \
                patch(f'{MODULO}.proponer_personajes', return_value=list(nuevos)), \
                patch(f'{MODULO}.proponer_primeras_apariciones', return_value=propuestas) as ia, \
                patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test'}):
            call_command('importar_personajes', obra='saga', sin_jikan=True, **opciones)
        return ia

    def test_wikidata_por_pelicula_entra_aprobado_y_ancla_la_unidad(self):
        self._importar({})
        heroina = Personaje.objects.get(wikidata_id='Q100')
        self.assertEqual(list(heroina.unidades.all()), [self.u1])
        self.assertTrue(ExternalId.objects.filter(source='wikidata', external_id='Q10', unidad=self.u1).exists())

    def test_descarta_partes_de_television_en_una_obra_de_peliculas(self):
        self._importar({})
        self.assertFalse(Personaje.objects.filter(wikidata_id='Q300').exists())

    def test_haiku_propone_para_todos_y_solo_se_guarda_lo_que_adelanta(self):
        ia = self._importar({
            0: {'unidad_id': self.u2.id, 'confianza': 0.9, 'nombre': 'Heroína', 'nota': 'tarde'},
            1: {'unidad_id': self.u2.id, 'confianza': 0.7, 'nombre': 'Villano', 'nota': 'x'},
        })

        self.assertEqual(set(ia.call_args.args[1].values()), {'Heroína', 'Villano'})
        heroina = Personaje.objects.get(wikidata_id='Q100')
        self.assertFalse(heroina.propuestas.filter(origen=PropuestaAparicion.ORIGEN_IA).exists())

        villano = Personaje.objects.get(wikidata_id='Q200')
        propuesta = villano.propuestas.get()
        self.assertEqual((propuesta.unidad, propuesta.estado), (self.u2, PropuestaAparicion.ESTADO_PENDIENTE))
        self.assertFalse(villano.unidades.exists())

    def test_completar_ia_anade_candidatos_para_proponer_su_aparicion(self):
        ia = self._importar({}, nuevos=['Mentor'], completar_ia=5)
        self.assertIn('Mentor', ia.call_args.args[1].values())

    def test_lista_de_obra_demasiado_larga_se_ignora(self):
        ia = self._importar({}, max_wikidata=1)
        self.assertNotIn('Villano', ia.call_args.args[1].values())

    def test_dry_run_no_escribe_nada(self):
        ia = self._importar({}, dry_run=True)
        ia.assert_not_called()
        self.assertFalse(Personaje.objects.exists())