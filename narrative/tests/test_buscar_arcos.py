from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, UnidadNarrativa
from narrative.services import actualizar_progreso
from posts.tests.utils import crear_post
from subscriptions.services import crear_suscripcion


def _obra_con_arcos(slug):
    """Tres arcos de dos episodios: posiciones 1-2, 3-4 y 5-6."""
    obra = Obra.objects.create(titulo=slug, slug=slug)
    arcos = [
        UnidadNarrativa.objects.create(obra=obra, tipo='arco', nombre=f'Arco {n}', orden_local=n)
        for n in (1, 2, 3)
    ]
    episodios = [
        UnidadNarrativa.objects.create(
            obra=obra, padre=arcos[i // 2], tipo='episodio', nombre=f'Episodio {i + 1}', orden_local=i % 2 + 1,
        )
        for i in range(6)
    ]
    obra.recalcular_orden()
    for unidad in arcos + episodios:
        unidad.refresh_from_db()
    return obra, arcos, episodios


class BuscarArcosTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('buscador_arcos', password='x')
        self.obra, self.arcos, self.eps = _obra_con_arcos('busqueda-arcos')
        actualizar_progreso(self.usuario, self.obra, self.eps[2])
        self.client.force_authenticate(user=self.usuario)

    def _arcos(self, q):
        return self.client.get(reverse('narrative_api_buscar'), {'q': q}).data['arcos']

    def test_solo_arcos_ya_empezados(self):
        self.assertEqual([a['nombre'] for a in self._arcos('arco')], ['Arco 1', 'Arco 2'])

    def test_nunca_devuelve_episodios(self):
        self.assertEqual(self._arcos('episodio'), [])

    def test_sin_progreso_no_devuelve_arcos(self):
        otro = APIClient()
        otro.force_authenticate(user=User.objects.create_user('sin_progreso_arcos', password='x'))
        self.assertEqual(otro.get(reverse('narrative_api_buscar'), {'q': 'arco'}).data['arcos'], [])

    def test_refleja_la_suscripcion_al_arco(self):
        suscripcion = crear_suscripcion(self.usuario, self.obra, unidad=self.arcos[0])
        arco = self._arcos('arco 1')[0]
        self.assertTrue(arco['suscrito'])
        self.assertEqual(arco['suscripcion_id'], suscripcion.id)
        self.assertEqual(arco['obra_slug'], self.obra.slug)


class ArcoAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('lector_arco', password='x')
        self.obra, self.arcos, self.eps = _obra_con_arcos('arco-contexto')
        actualizar_progreso(self.usuario, self.obra, self.eps[2])
        self.client.force_authenticate(user=self.usuario)

    def _arco(self, arco):
        return self.client.get(reverse('narrative_api_arco', args=[arco.id]))

    def test_arco_empezado_devuelve_su_contexto(self):
        response = self._arco(self.arcos[1])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['nombre'], 'Arco 2')

    def test_arco_no_empezado_da_404(self):
        self.assertEqual(self._arco(self.arcos[2]).status_code, 404)


class FeedPorArcoTests(TestCase):
    def test_filtra_los_posts_anclados_dentro_del_arco(self):
        usuario = User.objects.create_user('feed_por_arco', password='x')
        obra, arcos, eps = _obra_con_arcos('feed-por-arco')
        actualizar_progreso(usuario, obra, eps[2])
        dentro = crear_post(usuario, obra, eps[0])
        fuera = crear_post(usuario, obra, eps[2])

        cliente = APIClient()
        cliente.force_authenticate(user=usuario)
        response = cliente.get(reverse('narrative_api_feed'), {'unidad': arcos[0].id})
        ids = [p['id'] for p in response.data['results']]
        self.assertIn(dentro.id, ids)
        self.assertNotIn(fuera.id, ids)