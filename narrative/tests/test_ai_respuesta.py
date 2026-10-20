from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings

from narrative.ai_assistant import RespuestaInvalida, _resolver, proponer_clasificacion
from posts.tests.utils import crear_obra

OBJETIVO = 'narrative.ai_assistant.llamar_claude'


def _respuesta(entrada):
    return SimpleNamespace(content=[SimpleNamespace(type='tool_use', input=entrada)])


class ResolverRespuestaTests(TestCase):
    def setUp(self):
        self.obra, self.eps = crear_obra('respuesta-ia', 3)
        self.unidades = {u.id: u for u in self.eps}

    def _entrada(self, revelaciones):
        return {'parte_id': self.eps[0].id, 'revelaciones': revelaciones, 'confianza': 0.9}

    def test_respuesta_valida_toma_la_revelacion_mas_tardia(self):
        entrada = self._entrada([{'hecho': 'x', 'unidad_id': self.eps[2].id, 'confianza': 0.9}])
        self.assertEqual(_resolver(entrada, self.unidades, None).frontera_spoiler, self.eps[2])

    def test_revelacion_con_formato_invalido_descarta_la_propuesta(self):
        with self.assertRaises(RespuestaInvalida):
            _resolver(self._entrada(['texto suelto']), self.unidades, None)

    def test_id_inexistente_descarta_la_propuesta(self):
        with self.assertRaises(RespuestaInvalida):
            _resolver(self._entrada([{'hecho': 'x', 'unidad_id': 999999, 'confianza': 0.9}]), self.unidades, None)

    def test_proponer_devuelve_sugerencia_vacia_ante_respuesta_invalida(self):
        with patch(OBJETIVO, return_value=_respuesta(self._entrada(['texto suelto']))):
            self.assertIsNone(proponer_clasificacion('texto', self.obra).frontera_spoiler)


class PeticionTests(TestCase):
    @override_settings(IA_MODELO_FRONTERAS='modelo-de-fronteras')
    def test_usa_el_modelo_de_fronteras_indica_la_version_y_cachea_las_unidades(self):
        obra, eps = crear_obra('peticion-ia', 2)
        entrada = {'parte_id': eps[0].id, 'revelaciones': [], 'confianza': 0.9}
        with patch(OBJETIVO, return_value=_respuesta(entrada)) as llamada:
            proponer_clasificacion('texto', obra)

        parametros = llamada.call_args.kwargs
        contexto, peticion = parametros['messages'][0]['content']
        self.assertEqual(parametros['model'], 'modelo-de-fronteras')
        self.assertEqual(contexto['cache_control'], {'type': 'ephemeral'})
        self.assertIn('versión: Serie', contexto['text'])
        self.assertIn('texto', peticion['text'])