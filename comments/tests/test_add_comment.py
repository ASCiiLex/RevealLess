from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from posts.models import Post
from ..models import Comment


class AddCommentViewTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('add_comment_autor', password='x')
        self.comentador = User.objects.create_user('add_comment_comentador', password='x')

        self.obra = Obra.objects.create(titulo='Serie Add Comment', slug='serie-add-comment')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        actualizar_progreso(self.comentador, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='post base',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.client.force_login(self.comentador)

    def _comentar(self, text, **extra):
        return self.client.post(reverse('add_comment'), {'post_id': self.post.id, 'text': text, **extra})

    def _crear(self, text, parent=None, user=None):
        return Comment.objects.create(
            user=user or self.autor, post=self.post, parent=parent, text=text,
            referencia_narrativa=self.e1,
        )

    def test_crear_comentario_no_falla_por_referencia_narrativa_faltante(self):
        """Regresión: add_comment() no asignaba referencia_narrativa (NOT NULL)."""
        self.assertEqual(self._comentar('un comentario cualquiera').status_code, 200)

    def test_comentario_creado_hereda_referencia_narrativa_del_post(self):
        self._comentar('hereda referencia')
        comentario = Comment.objects.get(text='hereda referencia')
        self.assertEqual(comentario.referencia_narrativa, self.post.referencia_narrativa)

    def test_comentario_creado_hereda_frontera_del_post_por_defecto(self):
        self._comentar('hereda frontera')
        comentario = Comment.objects.get(text='hereda frontera')
        self.assertEqual(comentario.frontera_origen, ClasificacionNarrativa.ORIGEN_HEREDADO_POST)
        self.assertEqual(comentario.frontera_efectiva_orden, self.post.frontera_orden)

    def test_respuesta_incluye_datos_del_comentario(self):
        datos = self._comentar('respuesta json').json()
        self.assertEqual(datos['text'], 'respuesta json')
        self.assertEqual(datos['user'], self.comentador.username)

    def test_rechaza_texto_vacio(self):
        self.assertEqual(self._comentar('').status_code, 400)

    def test_rechaza_post_id_no_numerico(self):
        response = self.client.post(reverse('add_comment'), {'post_id': 'abc', 'text': 'x'})
        self.assertEqual(response.status_code, 400)

    def test_crear_reply_hereda_referencia_narrativa_del_post(self):
        padre = self._crear('padre')
        response = self._comentar('una respuesta', parent_id=padre.id)
        self.assertEqual(response.status_code, 200)
        reply = Comment.objects.get(text='una respuesta')
        self.assertEqual(reply.parent, padre)
        self.assertEqual(reply.referencia_narrativa, self.post.referencia_narrativa)

    def test_crear_comentario_con_emocion_autor(self):
        response = self._comentar('con emocion', emocion_autor='me_da_miedo')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['emocion_autor'], 'me_da_miedo')

    def test_rechaza_emocion_autor_invalida_en_comentario(self):
        self.assertEqual(self._comentar('emocion mala', emocion_autor='inventada').status_code, 400)

    def test_responder_a_una_respuesta_de_segundo_nivel_crea_nivel_3(self):
        """Nivel 3 (raíz -> respuesta -> respuesta) es el máximo permitido."""
        nivel_2 = self._crear('respuesta nivel 2', parent=self._crear('comentario raiz'), user=self.comentador)
        response = self._comentar('respuesta nivel 3', parent_id=nivel_2.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.get(text='respuesta nivel 3').parent, nivel_2)

    def test_responder_a_una_respuesta_de_tercer_nivel_es_rechazado(self):
        nivel_2 = self._crear('respuesta nivel 2', parent=self._crear('comentario raiz'), user=self.comentador)
        nivel_3 = self._crear('respuesta nivel 3', parent=nivel_2, user=self.comentador)
        self.assertEqual(self._comentar('intento nivel 4', parent_id=nivel_3.id).status_code, 400)

    def test_crear_comentario_con_obra_cruzada_y_frontera(self):
        manga = Obra.objects.create(titulo='Manga X', slug='manga-x')
        cap = UnidadNarrativa.objects.create(obra=manga, tipo='capitulo', nombre='Cap 900', orden_local=1)
        manga.recalcular_orden()
        cap.refresh_from_db()

        response = self._comentar('esto es del manga', obra_cruzada=manga.id, frontera_cruzada=cap.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['obra_cruzada_id'], manga.id)
        self.assertEqual(response.json()['frontera_cruzada_id'], cap.id)

    def test_rechaza_obra_cruzada_sin_frontera_cruzada(self):
        manga = Obra.objects.create(titulo='Manga Y', slug='manga-y')
        self.assertEqual(self._comentar('incompleto', obra_cruzada=manga.id).status_code, 400)