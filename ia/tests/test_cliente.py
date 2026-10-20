import os
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from narrative.models import Obra
from ia.cliente import IANoConfigurada, coste_estimado, llamar_claude
from ia.models import UsoIA

PARAMETROS = {'model': 'claude-haiku-4-5-20251001', 'max_tokens': 10, 'messages': []}


def _respuesta(entrada=1000, salida=500):
    return SimpleNamespace(usage=SimpleNamespace(input_tokens=entrada, output_tokens=salida), content=[])


@patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'clave-de-prueba'})
class LlamarClaudeTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('usuario_ia', password='x')
        self.obra = Obra.objects.create(titulo='Obra IA', slug='obra-ia')

    def _llamar(self, cliente_falso, **extra):
        with patch('anthropic.Anthropic', return_value=cliente_falso):
            return llamar_claude(
                UsoIA.FUNCION_CLASIFICACION, usuario=self.usuario, obra=self.obra, **{**PARAMETROS, **extra},
            )

    def _cliente(self, respuesta=None, error=None):
        cliente = SimpleNamespace(messages=SimpleNamespace())
        if error:
            def fallar(**_):
                raise error
            cliente.messages.create = fallar
        else:
            cliente.messages.create = lambda **_: respuesta
        return cliente

    def test_registra_tokens_coste_usuario_y_obra(self):
        respuesta = _respuesta()
        self.assertIs(self._llamar(self._cliente(respuesta)), respuesta)

        uso = UsoIA.objects.get()
        self.assertEqual((uso.tokens_entrada, uso.tokens_salida), (1000, 500))
        self.assertEqual(uso.coste_estimado, Decimal('0.0035'))
        self.assertEqual((uso.usuario, uso.obra, uso.exito), (self.usuario, self.obra, True))

    def test_un_fallo_de_la_api_se_registra_y_se_propaga(self):
        with self.assertRaises(ValueError):
            self._llamar(self._cliente(error=ValueError('caída')))
        uso = UsoIA.objects.get()
        self.assertFalse(uso.exito)
        self.assertEqual(uso.tokens_entrada, 0)

    def test_si_falla_el_registro_la_llamada_sigue(self):
        respuesta = _respuesta()
        with patch('ia.models.UsoIA.objects.create', side_effect=RuntimeError('BD caída')):
            self.assertIs(self._llamar(self._cliente(respuesta)), respuesta)

    def test_modelo_sin_precio_guarda_tokens_sin_coste(self):
        self._llamar(self._cliente(_respuesta()), model='modelo-desconocido')
        uso = UsoIA.objects.get()
        self.assertEqual(uso.tokens_entrada, 1000)
        self.assertIsNone(uso.coste_estimado)


class ConfiguracionTests(TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_sin_clave_no_llama_ni_registra(self):
        with self.assertRaises(IANoConfigurada):
            llamar_claude(UsoIA.FUNCION_TRADUCCION, **PARAMETROS)
        self.assertFalse(UsoIA.objects.exists())

    @override_settings(IA_PRECIOS={'modelo-caro': (Decimal('10'), Decimal('20'))})
    def test_settings_amplia_la_tabla_de_precios(self):
        self.assertEqual(coste_estimado('modelo-caro-v2', 1_000_000, 1_000_000), Decimal('30'))