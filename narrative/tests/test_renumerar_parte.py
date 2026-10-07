from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from narrative.models import Obra, Personaje, UnidadNarrativa


class RenumerarParteTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo='Serie larga', slug='serie-larga')
        crear = UnidadNarrativa.objects.create
        primera = crear(obra=self.obra, tipo='parte', nombre='Primera', orden_local=1)
        t1 = crear(obra=self.obra, tipo='temporada', nombre='Temporada 1', orden_local=1, padre=primera)
        self.e1 = crear(obra=self.obra, tipo='episodio', nombre='Episodio 1', orden_local=1, padre=t1)
        crear(obra=self.obra, tipo='episodio', nombre='Episodio 2', orden_local=2, padre=t1)
        segunda = crear(obra=self.obra, tipo='parte', nombre='Segunda', orden_local=2)
        self.t2 = crear(obra=self.obra, tipo='temporada', nombre='Temporada 1', orden_local=1, padre=segunda)
        self.e3 = crear(obra=self.obra, tipo='episodio', nombre='Episodio 3', orden_local=1, padre=self.t2)
        self.e4 = crear(obra=self.obra, tipo='episodio', nombre='Episodio 4', orden_local=2, padre=self.t2)
        self.obra.recalcular_orden()
        self.e3.refresh_from_db()
        self.personaje = Personaje.objects.create(nombre='Testigo')
        self.personaje.unidades.add(self.e3)

    def _ejecutar(self, *extra):
        call_command('renumerar_parte', 'serie-larga', 'Segunda', *extra, stdout=StringIO())

    def _nombres(self, *unidades):
        return [UnidadNarrativa.objects.get(pk=u.pk).nombre for u in unidades]

    def test_reinicia_la_numeracion_y_prefija_temporadas(self):
        self._ejecutar('--prefijo-temporadas', 'Segunda')
        self.assertEqual(self._nombres(self.e3, self.e4, self.t2), ['Episodio 1', 'Episodio 2', 'Segunda · Temporada 1'])
        self.assertEqual(self._nombres(self.e1), ['Episodio 1'])

    def test_no_cambia_ids_orden_ni_apariciones(self):
        orden_antes = self.e3.orden_inicio
        self._ejecutar()
        self.e3.refresh_from_db()
        self.assertEqual(self.e3.orden_inicio, orden_antes)
        self.assertIn(self.e3, self.personaje.unidades.all())

    def test_dry_run_no_guarda(self):
        self._ejecutar('--dry-run', '--prefijo-temporadas', 'Segunda')
        self.assertEqual(self._nombres(self.e3, self.t2), ['Episodio 3', 'Temporada 1'])

    def test_es_idempotente(self):
        self._ejecutar('--prefijo-temporadas', 'Segunda')
        self._ejecutar('--prefijo-temporadas', 'Segunda')
        self.assertEqual(self._nombres(self.e3, self.t2), ['Episodio 1', 'Segunda · Temporada 1'])