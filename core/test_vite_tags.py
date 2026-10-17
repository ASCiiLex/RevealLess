import json
import tempfile
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase, override_settings

from core.templatetags import vite_tags

MANIFEST = {
    'src/landing.tsx': {
        'file': 'assets/landing.js',
        'css': ['assets/landing.css'],
        'imports': ['_global.js', '_AuthForm.js'],
        'isEntry': True,
    },
    '_global.js': {'file': 'assets/global.js', 'css': ['assets/global.css']},
    '_AuthForm.js': {'file': 'assets/AuthForm.js', 'css': ['assets/AuthForm.css'], 'imports': ['_global.js']},
}


@override_settings(DEBUG=False)
class ViteAssetProduccionTests(SimpleTestCase):
    def setUp(self):
        directorio = tempfile.TemporaryDirectory()
        self.addCleanup(directorio.cleanup)
        ruta = Path(directorio.name) / 'manifest.json'
        ruta.write_text(json.dumps(MANIFEST))
        parche = mock.patch.object(vite_tags, 'MANIFEST_PATH', ruta)
        parche.start()
        self.addCleanup(parche.stop)
        vite_tags._manifest.cache_clear()
        self.addCleanup(vite_tags._manifest.cache_clear)

    def test_enlaza_el_css_de_los_chunks_importados(self):
        html = vite_tags.vite_asset('src/landing.tsx')
        for css in ('global.css', 'AuthForm.css', 'landing.css'):
            self.assertIn(f'/static/frontend/dist/assets/{css}', html)

    def test_css_compartido_primero_y_sin_duplicados(self):
        html = vite_tags.vite_asset('src/landing.tsx')
        self.assertEqual(html.count('assets/global.css'), 1)
        self.assertLess(html.index('global.css'), html.index('landing.css'))

    def test_precarga_los_chunks_importados(self):
        html = vite_tags.vite_asset('src/landing.tsx')
        self.assertIn('rel="modulepreload" href="/static/frontend/dist/assets/global.js"', html)

    def test_entrada_inexistente(self):
        self.assertIn('entrada no encontrada', vite_tags.vite_asset('src/no_existe.tsx'))