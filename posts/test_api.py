from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from comments.models import Comment
from likes.models import PostReaction
from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from .models import Post


class PostCreateAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('publicador', password='x')

        self.obra = Obra.objects.create(titulo='Serie Publicar', slug='serie-publicar')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.e3 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E3', orden_local=3,
        )
        self.obra.recalcular_orden()
        for u in (self.e1, self.e2, self.e3):
            u.refresh_from_db()

    def test_requiere_autenticacion(self):
        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {'text': 'hola', 'referencia_narrativa': self.e1.id},
        )
        self.assertEqual(response.status_code, 403)

    def test_sin_progreso_previo_devuelve_409(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {'text': 'hola', 'referencia_narrativa': self.e1.id},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['detail'], 'progreso_requerido')

    def test_crea_post_con_frontera_explicita(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {
                'text': 'con frontera explicita', 'referencia_narrativa': self.e1.id,
                'frontera_spoiler': self.e2.id,
            },
        )
        self.assertEqual(response.status_code, 201)

        post = Post.objects.get(text='con frontera explicita')
        self.assertEqual(post.frontera_origen, ClasificacionNarrativa.ORIGEN_EXPLICITO)
        self.assertEqual(post.frontera_spoiler, self.e2)

    def test_sin_frontera_explicita_cae_a_fallback_sin_api_key(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {'text': 'sin frontera, va a fallback', 'referencia_narrativa': self.e1.id},
        )
        self.assertEqual(response.status_code, 201)

        post = Post.objects.get(text='sin frontera, va a fallback')
        self.assertEqual(post.frontera_origen, ClasificacionNarrativa.ORIGEN_FALLBACK)
        self.assertEqual(post.frontera_spoiler, self.e1)

    def test_actualiza_progreso_desde_el_formulario(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {
                'text': 'avanzando progreso', 'referencia_narrativa': self.e1.id,
                'frontera_spoiler': self.e2.id, 'nuevo_progreso': self.e2.id,
            },
        )

        from narrative.models import ProgresoUsuario
        progreso = ProgresoUsuario.objects.get(usuario=self.usuario, obra=self.obra)
        self.assertEqual(progreso.unidad_actual, self.e2)

    def test_salto_grande_de_progreso_devuelve_409(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        unidades_extra = []
        for i in range(4, 8):
            u = UnidadNarrativa.objects.create(
                obra=self.obra, tipo='episodio', nombre=f'E{i}', orden_local=i,
            )
            unidades_extra.append(u)
        self.obra.recalcular_orden()
        for u in unidades_extra:
            u.refresh_from_db()

        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {
                'text': 'salto grande', 'referencia_narrativa': self.e1.id,
                'frontera_spoiler': unidades_extra[-1].id, 'nuevo_progreso': unidades_extra[-1].id,
            },
        )
        self.assertEqual(response.status_code, 409)
        self.assertTrue(response.data['requiere_confirmacion_progreso'])

    def test_salto_grande_confirmado_se_aplica(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        unidades_extra = []
        for i in range(4, 8):
            u = UnidadNarrativa.objects.create(
                obra=self.obra, tipo='episodio', nombre=f'E{i}', orden_local=i,
            )
            unidades_extra.append(u)
        self.obra.recalcular_orden()
        for u in unidades_extra:
            u.refresh_from_db()

        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {
                'text': 'salto grande confirmado', 'referencia_narrativa': self.e1.id,
                'frontera_spoiler': unidades_extra[-1].id, 'nuevo_progreso': unidades_extra[-1].id,
                'confirmar_salto_progreso': 'true',
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_rechaza_texto_vacio(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {'text': '', 'referencia_narrativa': self.e1.id},
        )
        self.assertEqual(response.status_code, 400)


class PostDetailAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('detalle_autor', password='x')
        self.lector = User.objects.create_user('detalle_lector', password='x')

        self.obra = Obra.objects.create(titulo='Serie Detalle Post', slug='serie-detalle-post')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()

        # Progreso del lector alcanza e1: necesario para que el post
        # explicito con frontera=e1 sea realmente visible para el.
        # visible_for() exige progreso_lector >= frontera_orden, un
        # anonimo (progreso 0) nunca alcanzaria frontera_orden=e1.orden_fin.
        actualizar_progreso(self.lector, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='post de prueba',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_visible_para_usuario_con_progreso_suficiente(self):
        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)

    def test_anonimo_sin_progreso_recibe_404(self):
        """Un anonimo tiene progreso 0 -- nunca alcanza frontera_orden
        de un post con frontera > 0, ni siquiera uno explicito. Esto es
        el comportamiento correcto y ya probado de visible_for(), no
        una limitacion de PostDetailAPIView."""
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 404)

    def test_autor_ve_su_propio_post_sin_progreso(self):
        self.client.force_authenticate(user=self.autor)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)

    def test_devuelve_404_si_no_visible_para_el_usuario(self):
        post_bloqueado = Post.objects.create(
            author=self.autor, obra=self.obra, text='con spoiler',
            referencia_narrativa=self.e1, frontera_spoiler=self.e2,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[post_bloqueado.id]))
        self.assertEqual(response.status_code, 404)

    def test_incluye_datos_del_post(self):
        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(response.data['post']['id'], self.post.id)

    def test_incluye_comentarios_de_nivel_superior(self):
        Comment.objects.create(
            user=self.lector, post=self.post, text='un comentario',
            referencia_narrativa=self.e1,
        )
        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(len(response.data['comments']), 1)

    def test_incluye_replies_anidadas(self):
        padre = Comment.objects.create(
            user=self.lector, post=self.post, text='padre',
            referencia_narrativa=self.e1,
        )
        Comment.objects.create(
            user=self.autor, post=self.post, parent=padre, text='reply',
            referencia_narrativa=self.e1,
        )
        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(len(response.data['comments'][0]['replies']), 1)

    def test_incluye_user_reaction_del_post(self):
        PostReaction.objects.create(user=self.lector, post=self.post, reaction='love')
        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(response.data['post_reaction'], 'love')

    def test_post_reaction_es_none_sin_reaccion(self):
        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertIsNone(response.data['post_reaction'])

    def test_ordena_por_popular(self):
        c1 = Comment.objects.create(
            user=self.lector, post=self.post, text='poco popular',
            referencia_narrativa=self.e1,
        )
        c2 = Comment.objects.create(
            user=self.autor, post=self.post, text='muy popular',
            referencia_narrativa=self.e1,
        )
        from comments.models import CommentReaction
        CommentReaction.objects.create(user=self.autor, comment=c2, reaction='like')
        CommentReaction.objects.create(user=self.lector, comment=c2, reaction='love')

        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]), {'sort': 'popular'})
        self.assertEqual(response.data['comments'][0]['id'], c2.id)


class FeedUserReactionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('feed_reactor', password='x')
        self.obra = Obra.objects.create(titulo='Serie Feed Reaction', slug='serie-feed-reaction')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        actualizar_progreso(self.usuario, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.usuario, obra=self.obra, text='post con reaccion',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_feed_incluye_user_reaction_none_sin_reaccionar(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        post_data = next(p for p in response.data['results'] if p['id'] == self.post.id)
        self.assertIsNone(post_data['user_reaction'])

    def test_feed_incluye_user_reaction_correcta(self):
        PostReaction.objects.create(user=self.usuario, post=self.post, reaction='funny')
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        post_data = next(p for p in response.data['results'] if p['id'] == self.post.id)
        self.assertEqual(post_data['user_reaction'], 'funny')


class PostUpdateAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('editor_post', password='x')
        self.otro_usuario = User.objects.create_user('otro_editor_post', password='x')

        self.obra = Obra.objects.create(titulo='Serie Editar Post', slug='serie-editar-post')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='texto original',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_requiere_autenticacion(self):
        response = self.client.patch(
            reverse('posts_api_update', args=[self.post.id]), {'text': 'nuevo'},
        )
        self.assertEqual(response.status_code, 403)

    def test_solo_el_autor_puede_editar(self):
        self.client.force_authenticate(user=self.otro_usuario)
        response = self.client.patch(
            reverse('posts_api_update', args=[self.post.id]), {'text': 'intento ajeno'},
        )
        self.assertEqual(response.status_code, 403)

    def test_edita_el_texto(self):
        self.client.force_authenticate(user=self.autor)
        response = self.client.patch(
            reverse('posts_api_update', args=[self.post.id]), {'text': 'texto editado'},
        )
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, 'texto editado')

    def test_editar_frontera_marca_origen_explicito(self):
        self.client.force_authenticate(user=self.autor)
        self.client.patch(
            reverse('posts_api_update', args=[self.post.id]), {'frontera_spoiler': self.e2.id},
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.frontera_spoiler, self.e2)
        self.assertEqual(self.post.frontera_origen, ClasificacionNarrativa.ORIGEN_EXPLICITO)

    def test_sin_enviar_frontera_no_se_modifica(self):
        """Decision explicita: omitir frontera_spoiler en la edicion NO
        dispara recalculo con IA (a diferencia de la creacion) -- se
        interpreta como 'sin cambios'."""
        frontera_original = self.post.frontera_spoiler
        origen_original = self.post.frontera_origen

        self.client.force_authenticate(user=self.autor)
        self.client.patch(
            reverse('posts_api_update', args=[self.post.id]), {'text': 'solo cambio el texto'},
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.frontera_spoiler, frontera_original)
        self.assertEqual(self.post.frontera_origen, origen_original)

    def test_devuelve_404_si_el_post_no_existe(self):
        self.client.force_authenticate(user=self.autor)
        response = self.client.patch(
            reverse('posts_api_update', args=[999999]), {'text': 'x'},
        )
        self.assertEqual(response.status_code, 404)

    def test_edicion_parcial_no_requiere_todos_los_campos(self):
        self.client.force_authenticate(user=self.autor)
        response = self.client.patch(
            reverse('posts_api_update', args=[self.post.id]), {'nivel_spoiler': 'importante'},
        )
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.nivel_spoiler, 'importante')
        self.assertEqual(self.post.text, 'texto original')


class PostSerializerIsOwnPostTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('is_own_autor', password='x')
        self.otro = User.objects.create_user('is_own_otro', password='x')

        self.obra = Obra.objects.create(titulo='Serie Is Own', slug='serie-is-own')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        actualizar_progreso(self.autor, self.obra, self.e1)
        actualizar_progreso(self.otro, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='post propio',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_is_own_post_true_para_el_autor(self):
        self.client.force_authenticate(user=self.autor)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertTrue(response.data['post']['is_own_post'])

    def test_is_own_post_false_para_otro_usuario(self):
        self.client.force_authenticate(user=self.otro)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertFalse(response.data['post']['is_own_post'])

    def test_is_own_post_false_para_anonimo(self):
        """Un anonimo tiene progreso 0 -- nunca alcanza frontera_orden
        de un post con frontera > 0 (mismo comportamiento ya confirmado
        en PostDetailAPIViewTests.test_anonimo_sin_progreso_recibe_404).
        No se puede comprobar is_own_post en un post que el anonimo ni
        siquiera puede ver -- el propio 404 ya demuestra que 'anonimo
        != autor' se resuelve correctamente antes de llegar al
        serializer."""
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 404)

class PostSerializerFronteraSpoilerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('frontera_serializer_autor', password='x')
        self.obra = Obra.objects.create(titulo='Serie Frontera Serializer', slug='serie-frontera-serializer')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()
        actualizar_progreso(self.autor, self.obra, self.e2)

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='post con frontera',
            referencia_narrativa=self.e1, frontera_spoiler=self.e2,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_incluye_frontera_spoiler_completa(self):
        self.client.force_authenticate(user=self.autor)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(response.data['post']['frontera_spoiler']['id'], self.e2.id)
        self.assertIn('orden_inicio', response.data['post']['frontera_spoiler'])