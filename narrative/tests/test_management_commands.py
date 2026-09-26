from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from ..models import Obra, UnidadNarrativa


class RecalcularOrdenCommandTests(TestCase):
    def setUp(self):
        self.obra_a = Obra.objects.create(titulo='Comando A', slug='comando-a')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra_a, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra_a, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.obra_b = Obra.objects.create(titulo='Comando B', slug='comando-b')
        self.f1 = UnidadNarrativa.objects.create(
            obra=self.obra_b, tipo='episodio', nombre='F1', orden_local=1,
        )

    def test_con_slug_recalcula_solo_esa_obra(self):
        salida = StringIO()
        call_command('recalcular_orden', 'comando-a', stdout=salida)

        self.e1.refresh_from_db()
        self.e2.refresh_from_db()
        self.assertEqual((self.e1.orden_inicio, self.e1.orden_fin), (1, 1))
        self.assertEqual((self.e2.orden_inicio, self.e2.orden_fin), (2, 2))
        self.assertIn('Recalculado: Comando A', salida.getvalue())

    def test_con_slug_no_toca_otras_obras(self):
        call_command('recalcular_orden', 'comando-a')

        self.f1.refresh_from_db()
        self.assertEqual(self.f1.orden_inicio, 0)  # default sin recalcular

    def test_sin_slug_recalcula_todas(self):
        salida = StringIO()
        call_command('recalcular_orden', stdout=salida)

        self.e1.refresh_from_db()
        self.f1.refresh_from_db()
        self.assertEqual(self.e1.orden_inicio, 1)
        self.assertEqual(self.f1.orden_inicio, 1)
        self.assertIn('Recalculado: Comando A', salida.getvalue())
        self.assertIn('Recalculado: Comando B', salida.getvalue())

    def test_slug_inexistente_lanza_command_error(self):
        with self.assertRaises(CommandError):
            call_command('recalcular_orden', 'no-existe')