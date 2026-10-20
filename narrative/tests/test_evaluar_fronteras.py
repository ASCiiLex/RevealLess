import os
import tempfile
from io import StringIO
from unittest.mock import patch

import yaml
from django.core.management import call_command
from django.test import TestCase

from narrative.ai_assistant import SugerenciaIA
from posts.tests.utils import crear_obra

OBJETIVO = 'narrative.management.commands.evaluar_fronteras.proponer_clasificacion'


class EvaluarFronterasTests(TestCase):
    def setUp(self):
        self.obra, self.eps = crear_obra('evaluacion-fronteras', 3)
        casos = [
            {'obra': self.obra.slug, 'texto': 'a', 'esperada': 'U2'},
            {'obra': self.obra.slug, 'texto': 'b', 'esperada': 'U3'},
            {'obra': self.obra.slug, 'texto': 'c', 'esperada': 'U1'},
            {'obra': self.obra.slug, 'texto': 'd', 'esperada': 'No existe'},
        ]
        archivo = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
        yaml.dump(casos, archivo, allow_unicode=True)
        archivo.close()
        self.addCleanup(os.unlink, archivo.name)
        self.ruta = archivo.name

    def _evaluar(self, propuestas):
        respuestas = iter(propuestas)
        salida, errores = StringIO(), StringIO()
        with patch(OBJETIVO, side_effect=lambda *a, **k: next(respuestas)):
            call_command('evaluar_fronteras', self.ruta, modelo=['modelo-prueba'], stdout=salida, stderr=errores)
        return salida.getvalue(), errores.getvalue()

    def test_clasifica_exacto_fuga_y_tarde(self):
        salida, _ = self._evaluar([
            SugerenciaIA(self.eps[1], 0.9),
            SugerenciaIA(self.eps[0], 0.8),
            SugerenciaIA(self.eps[2], 0.7),
        ])
        self.assertIn('Exactos: 1/3', salida)
        self.assertIn('Demasiado pronto (fuga): 1', salida)
        self.assertIn('Demasiado tarde: 1', salida)

    def test_omite_casos_con_unidades_inexistentes(self):
        _, errores = self._evaluar([SugerenciaIA()] * 3)
        self.assertIn('No existe', errores)

    def test_cuenta_las_llamadas_sin_respuesta(self):
        salida, _ = self._evaluar([SugerenciaIA()] * 3)
        self.assertIn('Sin respuesta: 3', salida)