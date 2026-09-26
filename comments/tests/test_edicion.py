from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from posts.models import Post
from ..models import Comment


class EdicionComentarioTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('editor_comentario', password='x')

        anime = Obra.objects.create(titulo='Anime Edicion', slug='anime-edicion-comentario')
        e1 = UnidadNarrativa.objects.create(obra=anime, tipo='episodio', nombre='E1', orden_local=1)
        anime.recalcular_orden()
        e1.refresh_from_db()

        self.manga = Obra.objects.create(titulo='Manga Edicion', slug='manga-edicion-comentario')
        self.cap = UnidadNarrativa.objects.create(obra=self.manga, tipo='capitulo', nombre='Cap 1', orden_local=1)
        self.manga.recalcular_orden()
        self.cap.refresh_from_db()

        post = Post.objects.create(
            author=self.autor, obra=anime, text='post',
            referencia_narrativa=e1, frontera_spoiler=e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.comment = Comment.objects.create(
            user=self.autor, post=post, text='comentario', referencia_narrativa=e1,
        )
        self.url = reverse('comment_api_update', args=[self.comment.id])

    def _editar(self, user=None, formato='json', **datos):
        self.client.force_authenticate(user=user or self.autor)
        return self.client.patch(self.url, datos, format=formato)

    def test_otro_usuario_no_puede_editar(self):
        intruso = User.objects.create_user('intruso_comentario', password='x')
        self.assertEqual(self._editar(user=intruso, text='hackeado').status_code, 403)

    def test_rechaza_obra_cruzada_sin_frontera(self):
        self.assertEqual(self._editar(obra_cruzada=self.manga.id).status_code, 400)
        self.comment.refresh_from_db()
        self.assertIsNone(self.comment.obra_cruzada)

    def test_acepta_obra_y_frontera_cruzadas_juntas(self):
        response = self._editar(obra_cruzada=self.manga.id, frontera_cruzada=self.cap.id)
        self.assertEqual(response.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.obra_cruzada, self.manga)

    def test_quitar_obra_cruzada_con_valores_vacios(self):
        """El frontend envía '' en multipart para quitar la referencia cruzada."""
        self.comment.obra_cruzada = self.manga
        self.comment.frontera_cruzada = self.cap
        self.comment.save()

        response = self._editar(formato='multipart', obra_cruzada='', frontera_cruzada='')
        self.assertEqual(response.status_code, 200)

        self.comment.refresh_from_db()
        self.assertIsNone(self.comment.obra_cruzada)
        self.assertIsNone(self.comment.frontera_cruzada)
        self.assertIsNone(self.comment.frontera_cruzada_orden)