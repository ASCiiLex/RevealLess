import os
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from narrative.models import Obra, UnidadNarrativa
from narrative.services.traduccion import extraer_traducciones

RUTA_TRADUCIR = 'narrative.management.commands.traducir_catalogo.traducir_textos'


def falsa_traduccion(textos):
    return {id_: f'ES {texto}' for id_, texto in textos.items()}


@mock.patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test'})
class TraducirCatalogoTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo='Obra', slug='obra', sinopsis='A pirate story.')
        self.titulo = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='The beginning', orden_local=1)
        self.provisional = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='Episodio 2', orden_local=2)

    def _ejecutar(self, *args):
        call_command('traducir_catalogo', *args, stdout=StringIO(), stderr=StringIO())

    def test_traduce_y_marca_sinopsis_y_titulos(self):
        with mock.patch(RUTA_TRADUCIR, side_effect=falsa_traduccion):
            self._ejecutar()

        self.obra.refresh_from_db()
        self.titulo.refresh_from_db()
        self.assertEqual(self.obra.sinopsis, 'ES A pirate story.')
        self.assertTrue(self.obra.traducido)
        self.assertEqual(self.titulo.nombre, 'ES The beginning')
        self.assertTrue(self.titulo.traducido)

    def test_omite_titulos_provisionales(self):
        with mock.patch(RUTA_TRADUCIR, side_effect=falsa_traduccion):
            self._ejecutar()

        self.provisional.refresh_from_db()
        self.assertEqual(self.provisional.nombre, 'Episodio 2')
        self.assertFalse(self.provisional.traducido)

    def test_segunda_ejecucion_no_vuelve_a_llamar_a_la_api(self):
        with mock.patch(RUTA_TRADUCIR, side_effect=falsa_traduccion):
            self._ejecutar()
        with mock.patch(RUTA_TRADUCIR, side_effect=falsa_traduccion) as traducir:
            self._ejecutar()
        traducir.assert_not_called()

    def test_dry_run_no_llama_a_la_api(self):
        with mock.patch(RUTA_TRADUCIR) as traducir:
            self._ejecutar('--dry-run')
        traducir.assert_not_called()


class ExtraerTraduccionesTests(TestCase):
    def test_descarta_ids_no_pedidos_y_textos_vacios(self):
        entrada = {'traducciones': [
            {'id': 1, 'texto': 'Uno'},
            {'id': 99, 'texto': 'Inventado'},
            {'id': 2, 'texto': '   '},
            {'texto': 'Sin id'},
        ]}
        self.assertEqual(extraer_traducciones(entrada, {1, 2}), {1: 'Uno'})