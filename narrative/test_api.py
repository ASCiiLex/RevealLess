from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from follows.models import Follow
from likes.models import PostReaction
from comments.models import Comment
from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa, TemaTransversal
from narrative.services import actualizar_progreso
from posts.models import Post
from subscriptions.models import Suscripcion
from subscriptions.services import crear_suscripcion


class FeedAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.usuario = User.objects.create_user('usuario_api', password='x')
        self.seguido = User.objects.create_user('seguido_api', password='x')
        self.desconocido = User.objects.create_user('desconocido_api', password='x')

        Follow.objects.create(follower=self.usuario, followed=self.seguido)

        self.obra = Obra.objects.create(titulo='Serie API', slug='serie-api')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.e2 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E2', orden_local=2)
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()

        actualizar_progreso(self.usuario, self.obra, self.e1)
        actualizar_progreso(self.seguido, self.obra, self.e1)

        # Post propio, con frontera por delante del propio progreso del usuario.
        self.post_propio = Post.objects.create(
            author=self.usuario, obra=self.obra, text='mi post adelantado',
            referencia_narrativa=self.e1, frontera_spoiler=self.e2,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        # Post de un seguido, visible con el progreso actual del usuario.
        self.post_seguido_visible = Post.objects.create(
            author=self.seguido, obra=self.obra, text='post seguido visible',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        # Post de un seguido, no visible (frontera por delante del progreso del usuario).
        self.post_seguido_no_visible = Post.objects.create(
            author=self.seguido, obra=self.obra, text='post seguido con spoiler',
            referencia_narrativa=self.e1, frontera_spoiler=self.e2,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        # Post de alguien no seguido: no debe aparecer aunque sea visible.
        self.post_desconocido = Post.objects.create(
            author=self.desconocido, obra=self.obra, text='post ajeno',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

        PostReaction.objects.create(user=self.seguido, post=self.post_propio, reaction='like')
        Comment.objects.create(
            user=self.seguido, post=self.post_propio, text='comentario',
            referencia_narrativa=self.e1,
        )

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('narrative_api_feed'))
        self.assertEqual(response.status_code, 403)

    def test_incluye_post_propio_aunque_no_visible_para_si_mismo(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertIn(self.post_propio.id, ids)

    def test_incluye_post_de_seguido_visible(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertIn(self.post_seguido_visible.id, ids)

    def test_excluye_post_de_seguido_no_visible(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertNotIn(self.post_seguido_no_visible.id, ids)

    def test_excluye_post_de_no_seguido(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertNotIn(self.post_desconocido.id, ids)

    def test_todos_los_posts_incluyen_likes_count_y_comments_count(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        for post_data in response.data['results']:
            self.assertIn('likes_count', post_data)
            self.assertIn('comments_count', post_data)

    def test_post_propio_refleja_conteos_correctos(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        post_data = next(p for p in response.data['results'] if p['id'] == self.post_propio.id)
        self.assertEqual(post_data['likes_count'], 1)
        self.assertEqual(post_data['comments_count'], 1)

    def test_filtra_por_obra_cuando_se_pasa_query_param(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'), {'obra': self.obra.id})
        ids = [p['id'] for p in response.data['results']]
        self.assertIn(self.post_propio.id, ids)
        self.assertIn(self.post_seguido_visible.id, ids)

    def test_filtro_por_obra_excluye_posts_de_otra_obra(self):
        otra_obra = Obra.objects.create(titulo='Otra obra', slug='otra-obra-feed')
        otra_unidad = UnidadNarrativa.objects.create(
            obra=otra_obra, tipo='episodio', nombre='X1', orden_local=1,
        )
        otra_obra.recalcular_orden()
        otra_unidad.refresh_from_db()

        post_otra_obra = Post.objects.create(
            author=self.usuario, obra=otra_obra, text='de otra obra',
            referencia_narrativa=otra_unidad, frontera_spoiler=otra_unidad,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'), {'obra': self.obra.id})
        ids = [p['id'] for p in response.data['results']]
        self.assertNotIn(post_otra_obra.id, ids)

    def test_sin_query_param_obra_devuelve_feed_completo(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertIn(self.post_propio.id, ids)


class SuscripcionesEnFeedTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.usuario = User.objects.create_user('lector_susc', password='x')
        self.autor = User.objects.create_user('autor_susc', password='x')
        # El usuario no sigue al autor: solo la suscripción debe traer sus posts.

        self.obra = Obra.objects.create(titulo='Serie Susc', slug='serie-susc')
        self.otra_obra = Obra.objects.create(titulo='Otra Susc', slug='otra-susc')

        self.arco = UnidadNarrativa.objects.create(obra=self.obra, tipo='arco', nombre='Arco', orden_local=1)
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, padre=self.arco, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, padre=self.arco, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.otro_arco = UnidadNarrativa.objects.create(obra=self.obra, tipo='arco', nombre='Otro arco', orden_local=2)
        self.e3 = UnidadNarrativa.objects.create(
            obra=self.obra, padre=self.otro_arco, tipo='episodio', nombre='E3', orden_local=1,
        )
        self.obra.recalcular_orden()
        for u in (self.arco, self.e1, self.e2, self.otro_arco, self.e3):
            u.refresh_from_db()

        self.tema = TemaTransversal.objects.create(obra=self.obra, nombre='Tema seguido')
        self.otro_tema = TemaTransversal.objects.create(obra=self.obra, nombre='Tema no seguido')

        # Progreso suficiente para ver todo lo publicado en e1/e2/e3 en esta prueba.
        actualizar_progreso(self.usuario, self.obra, self.e3)

    def _post(self, referencia, temas=None, obra=None):
        post = Post.objects.create(
            author=self.autor, obra=obra or self.obra, text='contenido',
            referencia_narrativa=referencia, frontera_spoiler=referencia,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        if temas:
            post.temas_transversales.set(temas)
        return post

    def test_suscripcion_a_obra_completa_trae_post_de_no_seguido(self):
        crear_suscripcion(self.usuario, self.obra)
        post = self._post(self.e1)

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertIn(post.id, ids)

    def test_suscripcion_a_unidad_trae_solo_lo_que_cae_en_rango(self):
        crear_suscripcion(self.usuario, self.obra, unidad=self.arco)
        post_dentro = self._post(self.e1)
        post_fuera = self._post(self.e3)  # pertenece a otro_arco, no a arco

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertIn(post_dentro.id, ids)
        self.assertNotIn(post_fuera.id, ids)

    def test_suscripcion_a_tema_trae_solo_posts_etiquetados(self):
        crear_suscripcion(self.usuario, self.obra, tema=self.tema)
        post_con_tema = self._post(self.e1, temas=[self.tema])
        post_sin_tema = self._post(self.e2)

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertIn(post_con_tema.id, ids)
        self.assertNotIn(post_sin_tema.id, ids)

    def test_feed_fusiona_propios_seguidos_y_suscripciones_sin_duplicar(self):
        Follow.objects.create(follower=self.usuario, followed=self.autor)
        crear_suscripcion(self.usuario, self.obra)

        post_propio = Post.objects.create(
            author=self.usuario, obra=self.obra, text='mio',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        # Este post entra tanto por "seguido" (Follow) como por "suscripción
        # a obra completa" (Suscripcion): no debe duplicarse en el feed.
        post_seguido_y_suscrito = self._post(self.e2)

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]

        self.assertIn(post_propio.id, ids)
        self.assertIn(post_seguido_y_suscrito.id, ids)
        self.assertEqual(ids.count(post_seguido_y_suscrito.id), 1)

    def test_suscripcion_no_es_via_lateral_para_saltarse_visible_for(self):
        """Estar suscrito a una obra no implica ver todo su contenido: la
        frontera de spoiler sigue mandando. Este test es el que demuestra
        que 'estoy suscrito' y 'puedo ver' son decisiones independientes."""
        usuario_sin_progreso = User.objects.create_user('sin_progreso_susc', password='x')
        crear_suscripcion(usuario_sin_progreso, self.obra)

        post_con_spoiler = self._post(self.e3)  # frontera = e3, por delante del progreso 0

        self.client.force_authenticate(user=usuario_sin_progreso)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertNotIn(post_con_spoiler.id, ids)


class SuscripcionesSilenciadasTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('lector_silencio', password='x')
        self.autor_seguido = User.objects.create_user('autor_silencio', password='x')

        Follow.objects.create(follower=self.usuario, followed=self.autor_seguido)

        self.obra = Obra.objects.create(titulo='Serie Silencio', slug='serie-silencio')
        self.tema = TemaTransversal.objects.create(obra=self.obra, nombre='Tema silenciado')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()

        actualizar_progreso(self.usuario, self.obra, self.e1)

    def test_post_de_seguido_se_oculta_si_coincide_con_tema_silenciado(self):
        """El post llega por dos vias: es de un usuario seguido, Y ademas
        pertenece a un tema con suscripcion silenciada. El silencio debe
        prevalecer sobre la via del seguido, ocultando el post por
        completo del feed."""
        crear_suscripcion(self.usuario, self.obra, tema=self.tema)
        suscripcion_tema = Suscripcion.objects.get(usuario=self.usuario, tema=self.tema)
        suscripcion_tema.activa = False
        suscripcion_tema.save(update_fields=['activa'])

        post = Post.objects.create(
            author=self.autor_seguido, obra=self.obra, text='sobre el tema silenciado',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        post.temas_transversales.set([self.tema])

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertNotIn(post.id, ids)

    def test_post_del_mismo_tema_sin_silenciar_sigue_visible(self):
        """Confirma que el silencio no oculta de más: solo afecta al
        alcance exacto de la suscripcion silenciada."""
        crear_suscripcion(self.usuario, self.obra, tema=self.tema)
        suscripcion_tema = Suscripcion.objects.get(usuario=self.usuario, tema=self.tema)
        suscripcion_tema.activa = False
        suscripcion_tema.save(update_fields=['activa'])

        otro_tema = TemaTransversal.objects.create(obra=self.obra, nombre='Tema sin silenciar')
        post = Post.objects.create(
            author=self.autor_seguido, obra=self.obra, text='sobre otro tema',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        post.temas_transversales.set([otro_tema])

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertIn(post.id, ids)

    def test_post_propio_tambien_se_oculta_si_esta_silenciado(self):
        """Confirmado explicitamente: silenciar un tema oculta incluso
        los posts propios sobre ese tema, sin excepcion por autoria."""
        crear_suscripcion(self.usuario, self.obra, tema=self.tema)
        suscripcion_tema = Suscripcion.objects.get(usuario=self.usuario, tema=self.tema)
        suscripcion_tema.activa = False
        suscripcion_tema.save(update_fields=['activa'])

        post_propio = Post.objects.create(
            author=self.usuario, obra=self.obra, text='mi propio post sobre el tema',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        post_propio.temas_transversales.set([self.tema])

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertNotIn(post_propio.id, ids)