from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from posts.models import Post
from .models import Comment


class AddCommentViewTests(TestCase):
    def setUp(self):
        self.client = self.client_class()
        self.autor = User.objects.create_user('add_comment_autor', password='x')
        self.comentador = User.objects.create_user('add_comment_comentador', password='x')

        self.obra = Obra.objects.create(titulo='Serie Add Comment', slug='serie-add-comment')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='post base',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_crear_comentario_no_falla_por_referencia_narrativa_faltante(self):
        """Bug real detectado: add_comment() nunca asignaba
        referencia_narrativa (obligatorio en ClasificacionNarrativa),
        causando IntegrityError (NOT NULL constraint failed) en
        cualquier intento de comentar. Este test evita que se
        reintroduzca esa regresion."""
        self.client.force_login(self.comentador)
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'un comentario cualquiera',
        })
        self.assertEqual(response.status_code, 200)

    def test_comentario_creado_hereda_referencia_narrativa_del_post(self):
        self.client.force_login(self.comentador)
        self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'hereda referencia',
        })
        comentario = Comment.objects.get(text='hereda referencia')
        self.assertEqual(comentario.referencia_narrativa, self.post.referencia_narrativa)

    def test_comentario_creado_hereda_frontera_del_post_por_defecto(self):
        self.client.force_login(self.comentador)
        self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'hereda frontera',
        })
        comentario = Comment.objects.get(text='hereda frontera')
        self.assertEqual(comentario.frontera_origen, ClasificacionNarrativa.ORIGEN_HEREDADO_POST)
        self.assertEqual(comentario.frontera_efectiva_orden, self.post.frontera_orden)

    def test_respuesta_incluye_datos_del_comentario(self):
        self.client.force_login(self.comentador)
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'respuesta json',
        })
        self.assertEqual(response.json()['text'], 'respuesta json')
        self.assertEqual(response.json()['user'], self.comentador.username)

    def test_rechaza_texto_vacio(self):
        self.client.force_login(self.comentador)
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': '',
        })
        self.assertEqual(response.status_code, 400)

    def test_crear_reply_hereda_referencia_narrativa_del_post(self):
        self.client.force_login(self.comentador)
        padre = Comment.objects.create(
            user=self.autor, post=self.post, text='padre',
            referencia_narrativa=self.e1,
        )
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'una respuesta', 'parent_id': padre.id,
        })
        self.assertEqual(response.status_code, 200)
        reply = Comment.objects.get(text='una respuesta')
        self.assertEqual(reply.parent, padre)
        self.assertEqual(reply.referencia_narrativa, self.post.referencia_narrativa)

    def test_crear_comentario_con_emocion_autor(self):
        self.client.force_login(self.comentador)
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'con emocion', 'emocion_autor': 'me_da_miedo',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['emocion_autor'], 'me_da_miedo')

    def test_rechaza_emocion_autor_invalida_en_comentario(self):
        self.client.force_login(self.comentador)
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'emocion mala', 'emocion_autor': 'inventada',
        })
        self.assertEqual(response.status_code, 400)

    def test_responder_a_una_respuesta_es_rechazado(self):
        """Limite de 3 niveles: comentario -> respuesta ->
        respuesta-a-respuesta, y ahi se para."""
        self.client.force_login(self.comentador)
        padre = Comment.objects.create(
            user=self.autor, post=self.post, text='comentario raiz',
            referencia_narrativa=self.e1,
        )
        respuesta = Comment.objects.create(
            user=self.comentador, post=self.post, parent=padre, text='respuesta nivel 2',
            referencia_narrativa=self.e1,
        )
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'intento nivel 4', 'parent_id': respuesta.id,
        })
        self.assertEqual(response.status_code, 400)

    def test_responder_a_un_comentario_raiz_permite_nivel_3(self):
        """Confirma explicitamente que SI se permite: responder a una
        respuesta de nivel 2 cuyo padre es un comentario raiz (nivel 1)
        -- eso crea el nivel 3, el limite maximo permitido."""
        self.client.force_login(self.comentador)
        padre = Comment.objects.create(
            user=self.autor, post=self.post, text='comentario raiz',
            referencia_narrativa=self.e1,
        )
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'respuesta nivel 2', 'parent_id': padre.id,
        })
        self.assertEqual(response.status_code, 200)

    def test_crear_comentario_con_obra_cruzada_y_frontera(self):
        from narrative.models import Obra, UnidadNarrativa
        manga = Obra.objects.create(titulo='Manga X', slug='manga-x')
        cap = UnidadNarrativa.objects.create(obra=manga, tipo='capitulo', nombre='Cap 900', orden_local=1)
        manga.recalcular_orden()
        cap.refresh_from_db()

        self.client.force_login(self.comentador)
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'esto es del manga',
            'obra_cruzada': manga.id, 'frontera_cruzada': cap.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['obra_cruzada_id'], manga.id)
        self.assertEqual(response.json()['frontera_cruzada_id'], cap.id)

    def test_rechaza_obra_cruzada_sin_frontera_cruzada(self):
        from narrative.models import Obra
        manga = Obra.objects.create(titulo='Manga Y', slug='manga-y')

        self.client.force_login(self.comentador)
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'incompleto', 'obra_cruzada': manga.id,
        })
        self.assertEqual(response.status_code, 400)


class DeteccionReferenciaCruzadaComentarioTests(TestCase):
    def setUp(self):
        self.client = self.client_class()
        self.autor = User.objects.create_user('deteccion_autor', password='x')
        self.comentador = User.objects.create_user('deteccion_comentador', password='x')

        self.anime = Obra.objects.create(titulo='Anime Y', slug='anime-y', tipo=Obra.TIPO_SERIE)
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.anime, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.anime.recalcular_orden()
        self.e1.refresh_from_db()

        self.manga = Obra.objects.create(
            titulo='Manga Y', slug='manga-y-rel', tipo=Obra.TIPO_MANGA, adapta_a=self.anime,
        )
        self.cap = UnidadNarrativa.objects.create(
            obra=self.manga, tipo='capitulo', nombre='Cap 900', orden_local=1,
        )
        self.manga.recalcular_orden()
        self.cap.refresh_from_db()

        self.post = Post.objects.create(
            author=self.autor, obra=self.anime, text='post base',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_deteccion_bloquea_comentario_y_devuelve_detecciones(self):
        self.client.force_login(self.comentador)
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'esto pasó en el manga',
        })
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['detail'], 'referencia_cruzada_detectada')
        self.assertFalse(Comment.objects.filter(text='esto pasó en el manga').exists())

    def test_descartar_referencia_cruzada_permite_comentar(self):
        self.client.force_login(self.comentador)
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'esto pasó en el manga',
            'descartar_referencia_cruzada': 'true',
        })
        self.assertEqual(response.status_code, 200)
        comentario = Comment.objects.get(text='esto pasó en el manga')
        self.assertIsNone(comentario.obra_cruzada)

    def test_obra_cruzada_explicita_evita_la_deteccion(self):
        self.client.force_login(self.comentador)
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'esto pasó en el manga',
            'obra_cruzada': self.manga.id, 'frontera_cruzada': self.cap.id,
        })
        self.assertEqual(response.status_code, 200)
        comentario = Comment.objects.get(text='esto pasó en el manga')
        self.assertEqual(comentario.obra_cruzada, self.manga)