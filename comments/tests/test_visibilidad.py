from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase

from narrative.models import Obra, ProgresoUsuario, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from posts.models import Post
from posts.tests.utils import crear_obra
from ..models import Comment


class VisibilidadCommentTests(TestCase):
    def setUp(self):
        self.autor_post = User.objects.create_user('autor_post', password='x')
        self.lector_avanzado = User.objects.create_user('avanzado', password='x')
        self.lector_atrasado = User.objects.create_user('atrasado', password='x')

        self.obra = Obra.objects.create(titulo='Serie', slug='serie')
        self.e1, self.e2, self.e3 = (
            UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre=f'E{n}', orden_local=n)
            for n in (1, 2, 3)
        )
        self.obra.recalcular_orden()
        for u in (self.e1, self.e2, self.e3):
            u.refresh_from_db()

        actualizar_progreso(self.lector_avanzado, self.obra, self.e3)
        actualizar_progreso(self.lector_atrasado, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.autor_post, obra=self.obra, text='post',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.comentario_restrictivo = Comment.objects.create(
            user=self.autor_post, post=self.post, text='comentario spoiler',
            referencia_narrativa=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
            frontera_spoiler=self.e3,
        )

    def test_comentario_no_visible_si_no_alcanza_su_propia_frontera(self):
        self.assertNotIn(self.comentario_restrictivo, Comment.objects.visible_for(self.lector_atrasado))

    def test_comentario_visible_si_alcanza_su_propia_frontera(self):
        self.assertIn(self.comentario_restrictivo, Comment.objects.visible_for(self.lector_avanzado))

    def test_comentario_nunca_visible_si_su_post_no_lo_es(self):
        post_bloqueado = Post.objects.create(
            author=self.autor_post, obra=self.obra, text='post bloqueado',
            referencia_narrativa=self.e1, frontera_spoiler=self.e3,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        comentario = Comment.objects.create(
            user=self.autor_post, post=post_bloqueado, text='inofensivo',
            referencia_narrativa=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
            frontera_spoiler=self.e1,
        )
        self.assertNotIn(comentario, Comment.objects.visible_for(self.lector_atrasado))

    def test_usuario_anonimo_no_ve_comentarios(self):
        self.assertFalse(Comment.objects.visible_for(AnonymousUser()).exists())


class VisibilidadComentarioHeredadoTests(TestCase):
    """El comentario heredado sigue la regla de su post, sin el privilegio del autor del post."""

    def setUp(self):
        self.manga, self.caps = crear_obra('manga-heredado', 3, tipo_unidad='capitulo', tipo=Obra.TIPO_MANGA)
        self.anime, self.eps = crear_obra('anime-heredado', 3, adapta_a=self.manga)
        self.autor = User.objects.create_user('autor_escena', password='x')
        self.comentarista = User.objects.create_user('comentarista', password='x')
        actualizar_progreso(self.autor, self.anime, self.eps[2])
        actualizar_progreso(self.autor, self.manga, self.caps[2])
        actualizar_progreso(self.comentarista, self.anime, self.eps[2])

    def _post_cruzado(self, modo):
        return Post.objects.create(
            author=self.autor, obra=self.anime, text='escena',
            referencia_narrativa=self.eps[1], frontera_spoiler=self.eps[1],
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
            obra_cruzada=self.manga, frontera_cruzada=self.caps[1], modo_cruce=modo,
        )

    def _comentar(self, post, frontera=None):
        clasificacion = {'frontera_origen': ClasificacionNarrativa.ORIGEN_HEREDADO_POST}
        if frontera:
            clasificacion = {
                'frontera_origen': ClasificacionNarrativa.ORIGEN_EXPLICITO,
                'frontera_spoiler': frontera,
            }
        return Comment.objects.create(
            user=self.comentarista, post=post, text='comentario',
            referencia_narrativa=post.referencia_narrativa, **clasificacion,
        )

    def _lector(self, nombre, anime=None, manga=None):
        lector = User.objects.create_user(nombre, password='x')
        if anime:
            actualizar_progreso(lector, self.anime, anime)
        if manga:
            actualizar_progreso(lector, self.manga, manga)
        return lector

    def test_misma_escena_lector_solo_del_manga_ve_el_comentario_heredado(self):
        post = self._post_cruzado(Post.MODO_MISMA_ESCENA)
        comentario = self._comentar(post)
        lector = self._lector('lector_manga', manga=self.caps[1])

        self.assertIn(post, Post.objects.visible_for(lector))
        self.assertIn(comentario, Comment.objects.visible_for(lector))

    def test_misma_escena_comentario_con_frontera_propia_del_anime_sigue_oculto(self):
        # Sin equivalencia capítulo ↔ episodio, la frontera propia no se traduce: se oculta.
        post = self._post_cruzado(Post.MODO_MISMA_ESCENA)
        comentario = self._comentar(post, frontera=self.eps[1])
        lector = self._lector('lector_manga_propia', manga=self.caps[2])

        self.assertNotIn(comentario, Comment.objects.visible_for(lector))

    def test_comparativa_sigue_exigiendo_ambas_fronteras(self):
        post = self._post_cruzado(Post.MODO_COMPARATIVA)
        comentario = self._comentar(post)
        solo_manga = self._lector('solo_manga', manga=self.caps[2])
        ambas = self._lector('ambas', anime=self.eps[1], manga=self.caps[1])

        self.assertNotIn(comentario, Comment.objects.visible_for(solo_manga))
        self.assertIn(comentario, Comment.objects.visible_for(ambas))

    def test_autor_que_retrocede_no_ve_comentarios_heredados_ajenos(self):
        post = Post.objects.create(
            author=self.autor, obra=self.anime, text='sin cruce',
            referencia_narrativa=self.eps[2], frontera_spoiler=self.eps[2],
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        comentario = self._comentar(post)
        ProgresoUsuario.objects.filter(usuario=self.autor, obra=self.anime).update(
            unidad_actual=self.eps[0], orden_absoluto=self.eps[0].orden_fin,
        )

        self.assertIn(post, Post.objects.visible_for(self.autor))
        self.assertNotIn(comentario, Comment.objects.visible_for(self.autor))