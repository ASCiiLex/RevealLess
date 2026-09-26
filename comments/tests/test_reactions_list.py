from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from posts.models import Post
from ..models import Comment, CommentReaction


class ListaReaccionesComentarioTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('lrc_autor', password='x')
        self.lector = User.objects.create_user('lrc_lector', password='x')

        self.obra = Obra.objects.create(titulo='Serie Lista Reacciones C', slug='serie-lista-reacciones-c')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        actualizar_progreso(self.lector, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='post base',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.comentario = Comment.objects.create(
            user=self.autor, post=self.post, text='comentario',
            referencia_narrativa=self.e1,
        )
        CommentReaction.objects.create(user=self.lector, comment=self.comentario, reaction='me_gusta')
        self.client.force_login(self.lector)
        self.url = reverse('comment_reactions_list', args=[self.comentario.id])

    def test_con_reacciones_existentes_responde_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_devuelve_totales_y_usuarios(self):
        data = self.client.get(self.url).json()
        self.assertEqual(set(data.keys()), {'totals', 'users'})
        self.assertEqual(data['totals']['me_gusta'], 1)

    def test_usuario_incluye_nombre_reaccion_y_perfil_react(self):
        usuario = self.client.get(self.url).json()['users'][0]
        self.assertEqual(usuario['username'], 'lrc_lector')
        self.assertEqual(usuario['reaction'], 'me_gusta')
        self.assertEqual(usuario['profile_url'], '/perfil/lrc_lector/')

    def test_avatar_es_url_absoluta(self):
        usuario = self.client.get(self.url).json()['users'][0]
        self.assertEqual(usuario['avatar_url'], 'http://testserver/static/img/default_profile.jpg')