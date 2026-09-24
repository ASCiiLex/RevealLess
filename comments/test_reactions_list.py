from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from posts.models import Post
from .models import Comment, CommentReaction


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

    def test_con_reacciones_existentes_responde_200(self):
        response = self.client.get(reverse('comment_reactions_list', args=[self.comentario.id]))
        self.assertEqual(response.status_code, 200)

    def test_devuelve_solo_los_totales(self):
        data = self.client.get(reverse('comment_reactions_list', args=[self.comentario.id])).json()
        self.assertEqual(set(data.keys()), {'totals'})
        self.assertEqual(data['totals']['me_gusta'], 1)