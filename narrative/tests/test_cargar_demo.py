import os
import tempfile
from io import StringIO

import yaml
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from narrative.models import ProgresoUsuario, UnidadNarrativa
from posts.models import Post
from posts.tests.utils import crear_obra


class CargarDemoTests(TestCase):
    def setUp(self):
        User.objects.create_user('autor_demo', password='x')
        self.lector = User.objects.create_user('lector_demo', password='x')
        self.obra, self.eps = crear_obra('obra-demo', 3)
        datos = {
            'previos': [{'obra': self.obra.slug, 'antes_de': 'U3', 'fecha': '2030-01-01'}],
            'progresos': [{'usuario': 'lector_demo', 'obra': self.obra.slug, 'hasta_previo_de': 'U3'}],
            'publicaciones': [{
                'autor': 'autor_demo', 'obra': self.obra.slug,
                'texto': 'Tráiler oficial', 'frontera': {'previo_de': 'U3'},
            }],
        }
        archivo = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
        yaml.dump(datos, archivo, allow_unicode=True)
        archivo.close()
        self.addCleanup(os.unlink, archivo.name)
        self.ruta = archivo.name

    def _cargar(self, *opciones):
        call_command('cargar_demo', self.ruta, *opciones, stdout=StringIO(), stderr=StringIO())

    def _previo(self):
        return UnidadNarrativa.objects.get(obra=self.obra, tipo=UnidadNarrativa.TIPO_PREVIO)

    def test_crea_previo_progreso_y_publicacion_visible_para_quien_llega(self):
        self._cargar()
        previo = self._previo()
        self.eps[1].refresh_from_db()
        self.assertEqual(previo.orden_frontera, self.eps[1].orden_fin)

        progreso = ProgresoUsuario.objects.get(usuario=self.lector, obra=self.obra)
        self.assertEqual(progreso.unidad_actual, self.eps[1])

        post = Post.objects.get()
        self.assertEqual(post.frontera_spoiler, previo)
        self.assertTrue(Post.objects.visible_for(self.lector).filter(pk=post.pk).exists())

    def test_es_idempotente(self):
        self._cargar()
        self._cargar()
        self.assertEqual(UnidadNarrativa.objects.filter(obra=self.obra, tipo=UnidadNarrativa.TIPO_PREVIO).count(), 1)
        self.assertEqual(Post.objects.count(), 1)

    def test_rehacer_vuelve_a_crear_las_publicaciones(self):
        self._cargar()
        primera = Post.objects.get().pk
        self._cargar('--rehacer')
        self.assertNotEqual(Post.objects.get().pk, primera)

    def test_sin_progresos_no_toca_el_progreso(self):
        self._cargar('--sin-progresos')
        self.assertFalse(ProgresoUsuario.objects.filter(usuario=self.lector).exists())