from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import Categoria, Obra, Personaje, ProgresoUsuario, UnidadNarrativa


class CategoriaLandingTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user('lector', password='x'))
        self.anime = Categoria.objects.create(nombre='Anime')
        self.dentro = Obra.objects.create(titulo='Dentro', slug='dentro')
        self.dentro.categorias.add(self.anime)
        Obra.objects.create(titulo='Fuera', slug='fuera')

    def test_devuelve_solo_las_obras_de_la_categoria(self):
        response = self.client.get(reverse('narrative_api_categoria_landing', args=[self.anime.id]))
        self.assertEqual(response.status_code, 200)
        datos = response.json()
        self.assertEqual(datos['nombre'], 'Anime')
        self.assertEqual([o['slug'] for o in datos['obras']], ['dentro'])

    def test_categoria_inexistente_da_404(self):
        response = self.client.get(reverse('narrative_api_categoria_landing', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_la_vista_react_monta_la_landing(self):
        response = self.client.get(reverse('narrative_categoria_landing', args=[self.anime.id]))
        self.assertContains(response, f'data-categoria-id="{self.anime.id}"')


class ObraLandingRelacionesTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('lectora', password='x')
        self.client.force_login(self.usuario)
        self.obra = Obra.objects.create(titulo='Obra', slug='obra')
        self.categoria = Categoria.objects.create(nombre='Series')
        self.obra.categorias.add(self.categoria)

        self.u1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='Uno', orden_local=1)
        self.u2 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='Dos', orden_local=2)
        self.obra.recalcular_orden()
        self.u1.refresh_from_db()
        self.u2.refresh_from_db()

        self.conocido = Personaje.objects.create(nombre='Conocido')
        self.conocido.unidades.add(self.u1)
        self.por_llegar = Personaje.objects.create(nombre='Por llegar')
        self.por_llegar.unidades.add(self.u2)

    def _landing(self):
        return self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug])).json()

    def test_categorias_incluyen_id_para_navegar(self):
        self.assertEqual(self._landing()['categorias_detalle'], [{'id': self.categoria.id, 'nombre': 'Series'}])

    def test_sin_progreso_no_se_muestran_personajes(self):
        self.assertEqual(self._landing()['personajes'], [])

    def test_solo_personajes_ya_aparecidos_segun_el_progreso(self):
        ProgresoUsuario.objects.create(
            usuario=self.usuario, obra=self.obra, unidad_actual=self.u1, orden_absoluto=self.u1.orden_fin,
        )
        self.assertEqual([p['nombre'] for p in self._landing()['personajes']], ['Conocido'])

    def test_obras_relacionadas_por_adaptacion(self):
        adaptacion = Obra.objects.create(titulo='Adaptación', slug='adaptacion', adapta_a=self.obra)
        self.assertEqual([o['slug'] for o in self._landing()['obras_relacionadas']], [adaptacion.slug])