from django.contrib.auth.models import User
from django.test import TestCase

from comments.models import Comment, CommentReaction
from likes.models import PostReaction
from ..models import Post
from .utils import crear_obra, crear_post


class FeedStatsQuerySetTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('autor_stats', password='x')
        self.otro = User.objects.create_user('otro_stats', password='x')
        self.tercero = User.objects.create_user('tercero_stats', password='x')

        obra, (self.e1,) = crear_obra('serie-stats')
        self.post = crear_post(self.autor, obra, self.e1, text='post con stats')

    def _comentar(self, user, text='comentario'):
        return Comment.objects.create(user=user, post=self.post, text=text, referencia_narrativa=self.e1)

    def _stats(self, qs=None):
        return (qs or Post.objects).with_feed_stats().get(pk=self.post.pk)

    def test_post_sin_interacciones_tiene_conteos_a_cero(self):
        post = self._stats()
        self.assertEqual(post.likes_count, 0)
        self.assertEqual(post.comments_count, 0)

    def test_conteos_correctos_con_likes_y_comentarios(self):
        PostReaction.objects.create(user=self.otro, post=self.post, reaction='like')
        PostReaction.objects.create(user=self.tercero, post=self.post, reaction='love')
        for user in (self.otro, self.tercero, self.autor):
            self._comentar(user)

        post = self._stats()
        self.assertEqual(post.likes_count, 2)
        self.assertEqual(post.comments_count, 3)

    def test_conteos_no_se_inflan_con_reacciones_a_comentarios(self):
        # Riesgo conocido: Count sobre relaciones distintas puede generar joins cartesianos.
        comment = self._comentar(self.otro)
        CommentReaction.objects.create(user=self.tercero, comment=comment, reaction='like')
        PostReaction.objects.create(user=self.otro, post=self.post, reaction='like')

        post = self._stats()
        self.assertEqual(post.likes_count, 1)
        self.assertEqual(post.comments_count, 1)

    def test_visible_for_y_with_feed_stats_se_combinan_sin_perder_anotaciones(self):
        PostReaction.objects.create(user=self.otro, post=self.post, reaction='like')
        self._comentar(self.otro)

        post = self._stats(Post.objects.visible_for(self.autor))
        self.assertEqual(post.likes_count, 1)
        self.assertEqual(post.comments_count, 1)