from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from posts.models import Post
from ..models import Categoria, Obra, TemaTransversal, UnidadNarrativa, ClasificacionNarrativa
from ..services import actualizar_progreso

TIPOS = ('obras', 'categorias', 'temas', 'usuarios')


class BuscarAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('buscador', password='x')
        self.obra = Obra.objects.create(titulo='One Piece', slug='one-piece')
        self.otra_obra = Obra.objects.create(titulo='Naruto', slug='naruto')
        self.tema = TemaTransversal.objects.create(obra=self.obra, nombre='Frutas del diablo')

    def _buscar(self, **params):
        self.client.force_authenticate(user=self.usuario)
        return self.client.get(reverse('narrative_api_buscar'), params)

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'one'})
        self.assertEqual(response.status_code, 403)

    def test_busca_obras_por_titulo_parcial(self):
        titulos = [o['titulo'] for o in self._buscar(q='one').data['obras']]
        self.assertIn('One Piece', titulos)
        self.assertNotIn('Naruto', titulos)

    def test_busca_temas_por_nombre_parcial(self):
        nombres = [t['nombre'] for t in self._buscar(q='fruta').data['temas']]
        self.assertIn('Frutas del diablo', nombres)

    def test_tema_incluye_datos_de_su_obra(self):
        tema_data = self._buscar(q='fruta').data['temas'][0]
        self.assertEqual(tema_data['obra_slug'], 'one-piece')
        self.assertEqual(tema_data['obra_titulo'], 'One Piece')

    def test_busqueda_case_insensitive(self):
        titulos = [o['titulo'] for o in self._buscar(q='ONE').data['obras']]
        self.assertIn('One Piece', titulos)

    def test_busca_categorias_con_su_total_de_obras(self):
        anime = Categoria.objects.create(nombre='Anime')
        self.obra.categorias.add(anime)
        self.otra_obra.categorias.add(anime)

        categorias = self._buscar(q='anim').data['categorias']
        self.assertEqual(categorias, [{'id': anime.id, 'nombre': 'Anime', 'total_obras': 2}])

    def test_query_corta_devuelve_listas_vacias_salvo_hashtags_sugeridos(self):
        data = self._buscar(q='o').data
        for tipo in TIPOS:
            self.assertEqual(data[tipo], [])

    def test_sin_query_devuelve_listas_vacias_salvo_hashtags_sugeridos(self):
        data = self._buscar().data
        for tipo in TIPOS:
            self.assertEqual(data[tipo], [])

    def test_query_sin_coincidencias_devuelve_listas_vacias(self):
        data = self._buscar(q='inexistente').data
        for tipo in (*TIPOS, 'hashtags'):
            self.assertEqual(data[tipo], [])

    def test_tema_incluye_suscrito_true_si_ya_esta_suscrito(self):
        from subscriptions.services import crear_suscripcion
        crear_suscripcion(self.usuario, self.obra, tema=self.tema)

        tema_data = self._buscar(q='fruta').data['temas'][0]
        self.assertTrue(tema_data['suscrito'])
        self.assertIsNotNone(tema_data['suscripcion_id'])

    def test_tema_incluye_suscrito_false_sin_suscripcion(self):
        tema_data = self._buscar(q='fruta').data['temas'][0]
        self.assertFalse(tema_data['suscrito'])
        self.assertIsNone(tema_data['suscripcion_id'])


class BuscarUsuariosHashtagsAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('buscador_extra', password='x')
        self.otro_usuario = User.objects.create_user('alexuser_prueba', password='x')

        self.obra = Obra.objects.create(titulo='Serie Busqueda', slug='serie-busqueda')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()

        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

    def _post(self, texto, autor=None):
        # Post.save() extrae los hashtags del texto; no se crean PostHashtag a mano.
        return Post.objects.create(
            author=autor or self.usuario, obra=self.obra, text=texto,
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def _buscar(self, **params):
        return self.client.get(reverse('narrative_api_buscar'), params)

    def test_busca_usuarios_por_username_parcial(self):
        usernames = [u['username'] for u in self._buscar(q='alexuser').data['usuarios']]
        self.assertIn('alexuser_prueba', usernames)

    def test_usuario_incluye_avatar_url(self):
        self.assertIn('avatar_url', self._buscar(q='alexuser').data['usuarios'][0])

    def test_busca_hashtags_por_nombre_parcial(self):
        self._post('usando #revealless', autor=self.otro_usuario)
        nombres = [h['name'] for h in self._buscar(q='reveal').data['hashtags']]
        self.assertIn('revealless', nombres)

    def test_no_devuelve_publicaciones(self):
        """El buscador no expone texto de publicaciones: se leen en el feed, filtradas por progreso."""
        self._post('una escena inolvidable')
        self.assertNotIn('posts', self._buscar(q='inolvidable').data)

    def test_hashtags_sugeridos_ordenados_por_uso_sin_query(self):
        for i in range(3):
            self._post(f'post {i} #popular')
        self._post('post raro #raro')

        nombres = [h['name'] for h in self._buscar().data['hashtags']]
        self.assertEqual(nombres[0], 'popular')

    def test_no_devuelve_hashtags_de_publicaciones_ocultas(self):
        e2 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E2', orden_local=2)
        self.obra.recalcular_orden()
        e2.refresh_from_db()
        Post.objects.create(
            author=self.otro_usuario, obra=self.obra, text='giro final #muereace',
            referencia_narrativa=e2, frontera_spoiler=e2,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

        self.assertNotIn('muereace', [h['name'] for h in self._buscar(q='muere').data['hashtags']])
        self.assertNotIn('muereace', [h['name'] for h in self._buscar().data['hashtags']])