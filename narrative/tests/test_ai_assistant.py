import os
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from narrative.ai_assistant import (
    CONFIANZA_MAX_SIN_NOMBRE, MODELO_IA, _candidatas, _parametros_modelo, _resolver,
    es_nombre_generico, proponer_clasificacion,
)


def _unidades(*ordenes):
    return {i: SimpleNamespace(id=i, nombre=f'Arco {i}', orden_fin=orden) for i, orden in enumerate(ordenes, start=1)}


def _revelacion(unidad_id, confianza=0.9):
    return {'hecho': f'hecho {unidad_id}', 'unidad_id': unidad_id, 'confianza': confianza}


class ResolverTests(SimpleTestCase):
    def setUp(self):
        self.u = _unidades(10, 20, 30, 40)

    def test_frontera_es_la_revelacion_mas_tardia(self):
        entrada = {'parte_id': 1, 'confianza': 0.95, 'revelaciones': [_revelacion(4, 0.8), _revelacion(3, 0.7)]}
        sugerencia = _resolver(entrada, self.u, None)
        self.assertEqual(sugerencia.frontera_spoiler, self.u[4])
        self.assertEqual(sugerencia.confianza, 0.7)
        self.assertEqual([r.unidad for r in sugerencia.revelaciones], [self.u[3], self.u[4]])

    def test_nunca_anterior_a_la_parte(self):
        entrada = {'parte_id': 1, 'confianza': 0.9, 'revelaciones': [_revelacion(2)]}
        self.assertEqual(_resolver(entrada, self.u, self.u[3]).frontera_spoiler, self.u[3])

    def test_sin_revelaciones_la_frontera_es_la_parte(self):
        sugerencia = _resolver({'parte_id': 2, 'confianza': 0.9, 'revelaciones': []}, self.u, None)
        self.assertEqual((sugerencia.frontera_spoiler, sugerencia.parte), (self.u[2], self.u[2]))

    def test_la_parte_del_autor_prevalece(self):
        sugerencia = _resolver({'parte_id': 1, 'confianza': 0.9, 'revelaciones': []}, self.u, self.u[2])
        self.assertEqual(sugerencia.parte, self.u[2])

    def test_id_inventado_invalida_la_propuesta(self):
        entrada = {'parte_id': 1, 'confianza': 0.9, 'revelaciones': [_revelacion(99)]}
        with self.assertRaises(RuntimeError):
            _resolver(entrada, self.u, None)

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': ''})
    def test_sin_api_key_no_es_utilizable(self):
        self.assertFalse(proponer_clasificacion('texto', obra=None).es_utilizable)


class UnidadesSinNombreTests(SimpleTestCase):
    def setUp(self):
        self.u = {
            1: SimpleNamespace(id=1, nombre='Arco de Water 7', orden_fin=10),
            2: SimpleNamespace(id=2, nombre='Episodio 227', orden_fin=20),
        }

    def test_frontera_sin_titulo_elegida_por_la_ia_no_se_aplica_sola(self):
        entrada = {'parte_id': 1, 'confianza': 0.9, 'revelaciones': [_revelacion(2, 0.75)]}
        sugerencia = _resolver(entrada, self.u, None)
        self.assertEqual(sugerencia.frontera_spoiler, self.u[2])
        self.assertEqual(sugerencia.confianza, CONFIANZA_MAX_SIN_NOMBRE)
        self.assertFalse(sugerencia.es_utilizable)

    def test_frontera_con_nombre_conserva_la_confianza(self):
        sugerencia = _resolver({'parte_id': 1, 'confianza': 0.9, 'revelaciones': []}, self.u, None)
        self.assertEqual(sugerencia.confianza, 0.9)
        self.assertTrue(sugerencia.es_utilizable)

    def test_la_parte_elegida_por_el_autor_no_se_penaliza(self):
        sugerencia = _resolver({'parte_id': 2, 'confianza': 0.9, 'revelaciones': []}, self.u, self.u[2])
        self.assertEqual(sugerencia.confianza, 0.9)

    def test_detecta_nombres_genericos(self):
        for nombre in ('Episodio 227', 'episodio 3', 'Capítulo 12', 'Cap. 4', 'Volumen 7', 'Chapter 10'):
            self.assertTrue(es_nombre_generico(SimpleNamespace(nombre=nombre)), nombre)
        for nombre in ('Arco de Water 7', 'Episodio 1: Romance Dawn', 'Temporada 1'):
            self.assertFalse(es_nombre_generico(SimpleNamespace(nombre=nombre)), nombre)


class CandidatasTests(SimpleTestCase):
    def test_excluye_las_unidades_que_abarcan_la_obra_entera(self):
        raiz = SimpleNamespace(orden_inicio=1, orden_fin=500)
        temporada = SimpleNamespace(orden_inicio=1, orden_fin=20)
        episodio = SimpleNamespace(orden_inicio=344, orden_fin=344)
        self.assertEqual(_candidatas([raiz, temporada, episodio]), [temporada, episodio])

    def test_obra_de_una_sola_unidad_la_conserva(self):
        pelicula = SimpleNamespace(orden_inicio=1, orden_fin=1)
        self.assertEqual(_candidatas([pelicula]), [pelicula])


class ParametrosModeloTests(SimpleTestCase):
    def test_haiku_4_fuerza_la_herramienta_y_es_determinista(self):
        parametros = _parametros_modelo(MODELO_IA)
        self.assertEqual(parametros['tool_choice']['type'], 'tool')
        self.assertEqual(parametros['temperature'], 0)

    def test_modelos_5_no_fuerzan_ni_fijan_temperatura_y_piensan_poco(self):
        parametros = _parametros_modelo('claude-sonnet-5-5')
        self.assertEqual(parametros['tool_choice'], {'type': 'auto'})
        self.assertNotIn('temperature', parametros)
        self.assertEqual(parametros['extra_body']['output_config']['effort'], 'low')