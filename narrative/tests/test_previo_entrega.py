import os
import tempfile
from datetime import timedelta
from io import StringIO

import yaml
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from narrative.models import ExternalId, Obra, ProgresoUsuario, UnidadNarrativa
from narrative.services import actualizar_progreso
from narrative.services.fronteras import previa_cerrada
from narrative.services.previos import crear_previo
from posts.models import Post
from posts.tests.utils import crear_post

HOY = timezone.localdate()


def _serie(slug):
    """Temporada 1 (E1, E2) y Temporada 2 (E3): posiciones 1, 2 y 3."""
    obra = Obra.objects.create(titulo=slug, slug=slug)
    t1 = UnidadNarrativa.objects.create(obra=obra, tipo='temporada', nombre='Temporada 1', orden_local=1)
    t2 = UnidadNarrativa.objects.create(obra=obra, tipo='temporada', nombre='Temporada 2', orden_local=2)
    e1 = UnidadNarrativa.objects.create(obra=obra, padre=t1, tipo='episodio', nombre='E1', orden_local=1)
    e2 = UnidadNarrativa.objects.create(obra=obra, padre=t1, tipo='episodio', nombre='E2', orden_local=2)
    e3 = UnidadNarrativa.objects.create(obra=obra, padre=t2, tipo='episodio', nombre='E3', orden_local=1)
    obra.recalcular_orden()
    for unidad in (t1, t2, e1, e2, e3):
        unidad.refresh_from_db()
    return obra, t2, (e1, e2, e3)


def _refrescar(*unidades):
    for unidad in unidades:
        unidad.refresh_from_db()


def _fijar_fecha(unidad, dias):
    # Solo la fecha: la instancia puede tener posiciones anteriores a crear el previo.
    unidad.fecha = HOY + timedelta(days=dias)
    unidad.save(update_fields=['fecha'])


class CrearPrevioTests(TestCase):
    def setUp(self):
        self.obra, self.t2, (self.e1, self.e2, self.e3) = _serie('previo-entrega')

    def test_queda_justo_antes_de_la_entrega(self):
        previo = crear_previo(self.t2)
        _refrescar(self.e2, self.e3)
        self.assertEqual(previo.nombre, 'Previo · Temporada 2')
        self.assertIsNone(previo.padre_id)
        self.assertEqual(self.e2.orden_inicio, 2)
        self.assertEqual(previo.orden_inicio, 3)
        self.assertEqual(self.e3.orden_inicio, 4)

    def test_es_idempotente(self):
        self.assertEqual(crear_previo(self.t2).id, crear_previo(self.t2).id)
        self.assertEqual(self.obra.unidades.filter(tipo=UnidadNarrativa.TIPO_PREVIO).count(), 1)

    def test_su_frontera_es_el_final_de_la_entrega_anterior(self):
        autor = User.objects.create_user('autor_previo_entrega', password='x')
        post = crear_post(autor, self.obra, crear_previo(self.t2))
        self.assertEqual(post.frontera_orden, 2)

    def test_antes_de_una_pelicula_suelta(self):
        saga = Obra.objects.create(titulo='Saga', slug='previo-saga')
        p1 = UnidadNarrativa.objects.create(obra=saga, tipo='pelicula', nombre='Película 1', orden_local=1)
        p2 = UnidadNarrativa.objects.create(obra=saga, tipo='pelicula', nombre='Película 2', orden_local=2)
        saga.recalcular_orden()

        previo = crear_previo(p2)
        _refrescar(p1, p2)
        self.assertEqual((p1.orden_inicio, previo.orden_inicio, p2.orden_inicio), (1, 2, 3))

    def test_hereda_la_fecha_de_su_primer_episodio(self):
        _fijar_fecha(self.e3, 10)
        self.assertEqual(crear_previo(self.t2).fecha, self.e3.fecha)

    def test_desplaza_el_progreso_declarado_con_su_unidad(self):
        lector = User.objects.create_user('lector_previo_entrega', password='x')
        actualizar_progreso(lector, self.obra, self.e3)
        crear_previo(self.t2)
        self.assertEqual(ProgresoUsuario.objects.get(usuario=lector, obra=self.obra).orden_absoluto, 4)


class PreviaCerradaTests(TestCase):
    def setUp(self):
        self.obra, t2, (_, _, self.e3) = _serie('previo-cierre')
        self.previo = crear_previo(t2)

    def test_sin_fechas_sigue_abierto(self):
        self.assertFalse(previa_cerrada(self.previo))

    def test_estreno_futuro_sigue_abierto(self):
        _fijar_fecha(self.e3, 5)
        self.assertFalse(previa_cerrada(self.previo))

    def test_se_cierra_al_estrenarse_el_episodio_siguiente(self):
        _fijar_fecha(self.e3, 0)
        self.assertTrue(previa_cerrada(self.previo))

    def test_se_cierra_con_su_propia_fecha_de_estreno(self):
        _fijar_fecha(self.previo, -1)
        self.assertTrue(previa_cerrada(self.previo))

    def test_una_unidad_normal_nunca_esta_cerrada(self):
        self.assertFalse(previa_cerrada(self.e3))


class PreviaCerradaAlPublicarTests(TestCase):
    def setUp(self):
        self.obra, t2, (_, e2, self.e3) = _serie('previo-publicar')
        self.previo = crear_previo(t2)
        self.autor = User.objects.create_user('autor_previo_publicar', password='x')
        actualizar_progreso(self.autor, self.obra, e2)
        self.client = APIClient()
        self.client.force_authenticate(user=self.autor)

    def _publicar(self):
        return self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {'text': 'qué ganas de la segunda temporada', 'frontera_spoiler': self.previo.id},
        )

    def test_con_el_previo_abierto_se_publica(self):
        _fijar_fecha(self.e3, 5)
        self.assertEqual(self._publicar().status_code, 201)

    def test_con_el_previo_cerrado_devuelve_400(self):
        _fijar_fecha(self.e3, -1)
        self.assertEqual(self._publicar().status_code, 400)
        self.assertFalse(Post.objects.exists())

    def test_el_buscador_de_fronteras_omite_el_previo_cerrado(self):
        _fijar_fecha(self.e3, -1)
        url = reverse('narrative_api_unidades_buscar', args=[self.obra.slug])
        como_parte = [u['id'] for u in self.client.get(url).data['unidades']]
        como_frontera = [u['id'] for u in self.client.get(url, {'frontera': '1'}).data['unidades']]
        self.assertIn(self.previo.id, como_parte)
        self.assertNotIn(self.previo.id, como_frontera)


class ImportadorRespetaPrevioTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo='Serie importada', slug='previo-importada')
        ExternalId.objects.create(source=ExternalId.SOURCE_MANUAL, external_id='previo-importada', obra=self.obra)
        datos = {
            'obra_external_id': {'source': ExternalId.SOURCE_MANUAL, 'external_id': 'previo-importada'},
            'nodos': [
                {'tipo': 'temporada', 'nombre': 'Temporada 1', 'orden_local': 1, 'hijos': [
                    {'tipo': 'episodio', 'nombre': 'E1', 'orden_local': 1},
                    {'tipo': 'episodio', 'nombre': 'E2', 'orden_local': 2},
                ]},
                {'tipo': 'temporada', 'nombre': 'Temporada 2', 'orden_local': 2, 'hijos': [
                    {'tipo': 'episodio', 'nombre': 'E3', 'orden_local': 1},
                ]},
            ],
        }
        archivo = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
        yaml.dump(datos, archivo, allow_unicode=True)
        archivo.close()
        self.addCleanup(os.unlink, archivo.name)
        self.ruta = archivo.name

    def _importar(self):
        call_command('importar_estructura', self.ruta, stdout=StringIO())

    def test_reimportar_conserva_el_previo_en_su_sitio(self):
        self._importar()
        previo = crear_previo(self.obra.unidades.get(nombre='Temporada 2'))
        self._importar()

        previo.refresh_from_db()
        e3 = self.obra.unidades.get(nombre='E3')
        self.assertEqual(self.obra.unidades.filter(tipo=UnidadNarrativa.TIPO_PREVIO).count(), 1)
        self.assertEqual(self.obra.unidades.count(), 6)
        self.assertEqual((previo.orden_inicio, e3.orden_inicio), (3, 4))