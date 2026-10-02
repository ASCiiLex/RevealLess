import tempfile
import textwrap
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from narrative.models import EtapaPersonaje, Personaje, PropuestaAparicion, RelevanciaPersonaje
from posts.tests.utils import crear_obra

YAML = '''
obras: [saga]
tipo_unidad: pelicula
coincidencia: exacta
nuevos: ["Shuri"]
relevancias:
  - {personaje: "Tony Stark", nivel: principal}
apariciones:
  - {personaje: "Tony Stark", unidades: ["U1", "U3"]}
etapas:
  - {personaje: "Tony Stark", tras: "U1", nota: "Yo soy Iron Man", nivel: protagonista}
'''


class CargarPersonajesTests(TestCase):
    def setUp(self):
        self.obra, self.u = crear_obra('saga', 3, tipo_unidad='pelicula')
        self.tony = Personaje.objects.create(nombre='Tony Stark')

    def _cargar(self, *args):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / 'datos.yaml'
            ruta.write_text(textwrap.dedent(YAML), encoding='utf-8')
            call_command('cargar_personajes', str(ruta), *args, stdout=StringIO())

    def test_carga_nuevos_relevancias_apariciones_y_etapas(self):
        self._cargar()
        self.assertTrue(Personaje.objects.filter(nombre='Shuri').exists())
        self.assertEqual(
            RelevanciaPersonaje.objects.get(personaje=self.tony, obra=self.obra).nivel,
            RelevanciaPersonaje.NIVEL_PRINCIPAL,
        )
        self.assertEqual(set(self.tony.unidades.all()), {self.u[0], self.u[2]})
        self.assertTrue(all(
            p.origen == PropuestaAparicion.ORIGEN_MANUAL and p.estado == PropuestaAparicion.ESTADO_APROBADA
            for p in self.tony.propuestas.all()
        ))
        etapa = EtapaPersonaje.objects.get(personaje=self.tony, visible_tras=self.u[0])
        self.assertEqual((etapa.nota, etapa.nivel), ('Yo soy Iron Man', RelevanciaPersonaje.NIVEL_PROTAGONISTA))

    def test_dry_run_no_guarda_nada(self):
        self._cargar('--dry-run')
        self.assertFalse(Personaje.objects.filter(nombre='Shuri').exists())
        self.assertFalse(RelevanciaPersonaje.objects.exists())
        self.assertFalse(self.tony.unidades.exists())
        self.assertFalse(EtapaPersonaje.objects.exists())

    def test_recargar_conserva_la_imagen_de_la_etapa(self):
        self._cargar()
        EtapaPersonaje.objects.filter(personaje=self.tony).update(imagen='cartel.jpg')
        self._cargar()
        self.assertEqual(EtapaPersonaje.objects.get(personaje=self.tony).imagen.name, 'cartel.jpg')