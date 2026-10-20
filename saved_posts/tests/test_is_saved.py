from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from posts.models import Post
from ..models import SavedPost


class EstadoGuardadoTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('is_saved_user', password='x')
        self.otro = User.objects.create_user('is_saved_otro', password='x')

        self.obra = Obra.objects.create(titulo='Serie Is Saved', slug='serie-is-saved')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        actualizar_progreso(self.usuario, self.obra, self.e1)
        actualizar_progreso(self.otro, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.usuario, obra=self.obra, text='post guardable',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.client.force_authenticate(user=self.usuario)

    def _post_del_feed(self):
        return self.client.get(reverse('narrative_api_feed')).data['results'][0]

    def test_feed_marca_no_guardado_por_defecto(self):
        self.assertFalse(self._post_del_feed()['is_saved'])

    def test_feed_marca_guardado(self):
        SavedPost.objects.create(user=self.usuario, post=self.post)
        self.assertTrue(self._post_del_feed()['is_saved'])

    def test_detalle_marca_guardado(self):
        SavedPost.objects.create(user=self.usuario, post=self.post)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertTrue(response.data['post']['is_saved'])

    def test_guardado_de_otro_usuario_no_cuenta(self):
        SavedPost.objects.create(user=self.otro, post=self.post)
        self.assertFalse(self._post_del_feed()['is_saved'])

    def test_guardar_devuelve_is_saved_true(self):
        response = self.client.post(reverse('saved_posts_api_toggle', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'is_saved': True})

    def test_quitar_devuelve_is_saved_false(self):
        SavedPost.objects.create(user=self.usuario, post=self.post)
        response = self.client.delete(reverse('saved_posts_api_toggle', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'is_saved': False})