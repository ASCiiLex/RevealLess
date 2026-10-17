from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from comments.models import Comment, CommentReaction
from likes.models import PostReaction
from narrative.models import ClasificacionNarrativa, Obra, UnidadNarrativa
from narrative.services import actualizar_progreso
from ..models import Post

FEED = '/narrative/api/feed/'


class TotalesReaccionesTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('tr_autor', password='x')
        self.lector = User.objects.create_user('tr_lector', password='x')
        self.obra = Obra.objects.create(titulo='Serie Totales', slug='serie-totales')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        actualizar_progreso(self.lector, self.obra, self.e1)

        self.posts = [self._post(f'post {i}') for i in range(3)]
        PostReaction.objects.create(user=self.lector, post=self.posts[0], reaction='me_gusta')
        PostReaction.objects.create(user=self.autor, post=self.posts[0], reaction='me_encanta')

    def _post(self, texto):
        return Post.objects.create(
            author=self.autor, obra=self.obra, text=texto,
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def _consultas_del_feed(self):
        with CaptureQueriesContext(connection) as consultas:
            self.client.get(FEED)
        return len(consultas)

    def test_el_feed_incluye_los_totales_de_cada_post(self):
        self.client.force_login(self.autor)
        resultados = {p['id']: p for p in self.client.get(FEED).json()['results']}
        totales = resultados[self.posts[0].id]['reacciones_totales']
        self.assertEqual((totales['me_gusta'], totales['me_encanta']), (1, 1))
        self.assertEqual(sum(resultados[self.posts[1].id]['reacciones_totales'].values()), 0)

    def test_las_consultas_del_feed_no_crecen_con_los_posts(self):
        self.client.force_login(self.autor)
        antes = self._consultas_del_feed()
        for i in range(3):
            PostReaction.objects.create(user=self.lector, post=self._post(f'extra {i}'), reaction='me_gusta')
        self.assertEqual(self._consultas_del_feed(), antes)

    def test_el_detalle_incluye_totales_del_post_y_de_los_comentarios(self):
        comentario = Comment.objects.create(
            user=self.autor, post=self.posts[0], text='comentario', referencia_narrativa=self.e1,
        )
        CommentReaction.objects.create(user=self.lector, comment=comentario, reaction='me_divierte')
        self.client.force_login(self.lector)
        data = self.client.get(f'/posts/api/{self.posts[0].id}/').json()
        self.assertEqual(data['post']['reacciones_totales']['me_gusta'], 1)
        self.assertEqual(data['comments'][0]['reacciones_totales']['me_divierte'], 1)
        self.assertEqual(data['comments'][0]['reactions_count'], 1)