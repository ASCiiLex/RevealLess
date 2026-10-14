import os
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from narrative.ai_assistant import _resolver, proponer_clasificacion


def _unidades(*ordenes):
    return {i: SimpleNamespace(id=i, orden_fin=orden) for i, orden in enumerate(ordenes, start=1)}


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