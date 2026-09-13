from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from posts.models import Hashtag, PostHashtag, Post
from .models import Obra, TemaTransversal, UnidadNarrativa, ClasificacionNarrativa
from .services import actualizar_progreso


class BuscarAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('buscador', password='x')
        self.obra = Obra.objects.create(titulo='One Piece', slug='one-piece')
        self.otra_obra = Obra.objects.create(titulo='Naruto', slug='naruto')
        self.tema = TemaTransversal.objects.create(obra=self.obra, nombre='Frutas del diablo')

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'one'})
        self.assertEqual(response.status_code, 403)

    def test_busca_obras_por_titulo_parcial(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'one'})
        titulos = [o['titulo'] for o in response.data['obras']]
        self.assertIn('One Piece', titulos)
        self.assertNotIn('Naruto', titulos)

    def test_busca_temas_por_nombre_parcial(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'fruta'})
        nombres = [t['nombre'] for t in response.data['temas']]
        self.assertIn('Frutas del diablo', nombres)

    def test_tema_incluye_datos_de_su_obra(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'fruta'})
        tema_data = response.data['temas'][0]
        self.assertEqual(tema_data['obra_slug'], 'one-piece')
        self.assertEqual(tema_data['obra_titulo'], 'One Piece')

    def test_busqueda_case_insensitive(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'ONE'})
        titulos = [o['titulo'] for o in response.data['obras']]
        self.assertIn('One Piece', titulos)

    def test_query_corta_devuelve_listas_vacias_salvo_hashtags_sugeridos(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'o'})
        self.assertEqual(response.data['obras'], [])
        self.assertEqual(response.data['temas'], [])
        self.assertEqual(response.data['usuarios'], [])
        self.assertEqual(response.data['posts'], [])

    def test_sin_query_devuelve_listas_vacias_salvo_hashtags_sugeridos(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'))
        self.assertEqual(response.data['obras'], [])
        self.assertEqual(response.data['temas'], [])
        self.assertEqual(response.data['usuarios'], [])
        self.assertEqual(response.data['posts'], [])

    def test_query_sin_coincidencias_devuelve_listas_vacias(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'inexistente'})
        self.assertEqual(response.data['obras'], [])
        self.assertEqual(response.data['temas'], [])
        self.assertEqual(response.data['usuarios'], [])
        self.assertEqual(response.data['hashtags'], [])
        self.assertEqual(response.data['posts'], [])


class BuscarUsuariosHashtagsPostsAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('buscador_extra', password='x')
        self.otro_usuario = User.objects.create_user('alexuser_prueba', password='x')

        self.obra = Obra.objects.create(titulo='Serie Busqueda', slug='serie-busqueda')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()

        actualizar_progreso(self.usuario, self.obra, self.e1)

    def test_busca_usuarios_por_username_parcial(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'alexuser'})
        usernames = [u['username'] for u in response.data['usuarios']]
        self.assertIn('alexuser_prueba', usernames)

    def test_usuario_incluye_avatar_url(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'alexuser'})
        self.assertIn('avatar_url', response.data['usuarios'][0])

    def test_busca_hashtags_por_nombre_parcial(self):
        # Post.save() extrae hashtags automaticamente del texto via
        # extract_hashtags() -- no hace falta (ni se debe) crear el
        # PostHashtag a mano, o choca con el que ya crea el propio save().
        Post.objects.create(
            author=self.otro_usuario, obra=self.obra, text='usando #revealless',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'reveal'})
        nombres = [h['name'] for h in response.data['hashtags']]
        self.assertIn('revealless', nombres)

    def test_busca_posts_visibles_por_texto_parcial(self):
        Post.objects.create(
            author=self.usuario, obra=self.obra, text='una escena inolvidable',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'inolvidable'})
        textos = [p['text'] for p in response.data['posts']]
        self.assertTrue(any('inolvidable' in t for t in textos))

    def test_no_incluye_posts_bloqueados_por_frontera_de_spoiler(self):
        """Corrección de seguridad respecto a global_search() original:
        un post cuyo texto coincide con la búsqueda, pero cuya frontera
        de spoiler el usuario aún no ha alcanzado, NO debe aparecer en
        los resultados -- ni siquiera su fragmento de texto."""
        Post.objects.create(
            author=self.otro_usuario, obra=self.obra, text='spoiler inolvidable del final',
            referencia_narrativa=self.e1, frontera_spoiler=self.e2,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'inolvidable'})
        textos = [p['text'] for p in response.data['posts']]
        self.assertFalse(any('inolvidable' in t for t in textos))

    def test_post_propio_visible_aunque_no_alcance_su_propia_frontera(self):
        """El autor siempre ve sus propios posts en la búsqueda, igual
        que en el feed -- visible_for() ya contempla ese caso."""
        post_propio = Post.objects.create(
            author=self.usuario, obra=self.obra, text='mi post adelantado unico',
            referencia_narrativa=self.e1, frontera_spoiler=self.e2,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'), {'q': 'adelantado'})
        ids = [p['id'] for p in response.data['posts']]
        self.assertIn(post_propio.id, ids)

    def test_hashtags_sugeridos_ordenados_por_uso_sin_query(self):
        for i in range(3):
            Post.objects.create(
                author=self.usuario, obra=self.obra, text=f'post {i} #popular',
                referencia_narrativa=self.e1, frontera_spoiler=self.e1,
                frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
            )

        Post.objects.create(
            author=self.usuario, obra=self.obra, text='post raro #raro',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_buscar'))
        nombres = [h['name'] for h in response.data['hashtags']]
        self.assertEqual(nombres[0], 'popular')