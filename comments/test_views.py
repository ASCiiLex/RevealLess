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