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

    def _landing(self, slug=None):
        return self.client.get(reverse('narrative_api_obra_landing', args=[slug or self.obra.slug])).json()

    def _slugs_relacionadas(self, slug=None):
        return sorted(o['slug'] for o in self._landing(slug)['obras_relacionadas'])

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
        self.assertEqual(self._slugs_relacionadas(), [adaptacion.slug])

    def test_adaptaciones_hermanas_se_relacionan(self):
        Obra.objects.create(titulo='Peli', slug='peli', adapta_a=self.obra)
        Obra.objects.create(titulo='Anime', slug='anime', adapta_a=self.obra)
        self.assertEqual(self._slugs_relacionadas('peli'), ['anime', 'obra'])

    def test_obras_del_mismo_universo_se_relacionan(self):
        universo = Categoria.objects.create(nombre='Tierra Media', es_universo=True)
        hobbit = Obra.objects.create(titulo='El Hobbit', slug='hobbit')
        hobbit.categorias.add(universo)
        self.obra.categorias.add(universo)
        self.assertEqual(self._slugs_relacionadas(), ['hobbit'])
        self.assertEqual(self._slugs_relacionadas('hobbit'), ['obra'])

    def test_categoria_normal_no_relaciona(self):
        otra = Obra.objects.create(titulo='Otra serie', slug='otra-serie')
        otra.categorias.add(self.categoria)
        self.assertEqual(self._slugs_relacionadas(), [])

    def test_adaptacion_y_universo_no_duplican(self):
        universo = Categoria.objects.create(nombre='Franquicia', es_universo=True)
        adaptacion = Obra.objects.create(titulo='Adaptación', slug='adaptacion', adapta_a=self.obra)
        adaptacion.categorias.add(universo)
        self.obra.categorias.add(universo)
        self.assertEqual(self._slugs_relacionadas(), ['adaptacion'])