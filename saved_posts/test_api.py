from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from posts.models import Post
from .models import SavedPost


class SavedPostListAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('guardador', password='x')
        self.otro_usuario = User.objects.create_user('otro_guardador', password='x')

        self.obra = Obra.objects.create(titulo='Serie Guardados', slug='serie-guardados')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()

        self.post = Post.objects.create(
            author=self.otro_usuario, obra=self.obra, text='post guardable',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('saved_posts_api_list'))
        self.assertEqual(response.status_code, 403)

    def test_lista_solo_los_guardados_del_usuario(self):
        SavedPost.objects.create(user=self.usuario, post=self.post)

        otro_post = Post.objects.create(
            author=self.otro_usuario, obra=self.obra, text='otro post',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        SavedPost.objects.create(user=self.otro_usuario, post=otro_post)

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('saved_posts_api_list'))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['post_id'], self.post.id)


class SavedPostToggleAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('toggler', password='x')

        self.obra = Obra.objects.create(titulo='Serie Toggle Save', slug='serie-toggle-save')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()

        self.post = Post.objects.create(
            author=self.usuario, obra=self.obra, text='post para guardar',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_requiere_autenticacion_para_guardar(self):
        response = self.client.post(reverse('saved_posts_api_toggle', args=[self.post.id]))
        self.assertEqual(response.status_code, 403)

    def test_post_guarda_el_post(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(reverse('saved_posts_api_toggle', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SavedPost.objects.filter(user=self.usuario, post=self.post).exists())

    def test_post_es_idempotente(self):
        self.client.force_authenticate(user=self.usuario)
        self.client.post(reverse('saved_posts_api_toggle', args=[self.post.id]))
        self.client.post(reverse('saved_posts_api_toggle', args=[self.post.id]))
        self.assertEqual(
            SavedPost.objects.filter(user=self.usuario, post=self.post).count(), 1
        )

    def test_delete_elimina_el_guardado(self):
        SavedPost.objects.create(user=self.usuario, post=self.post)
        self.client.force_authenticate(user=self.usuario)
        response = self.client.delete(reverse('saved_posts_api_toggle', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SavedPost.objects.filter(user=self.usuario, post=self.post).exists())

    def test_delete_sin_guardado_previo_no_falla(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.delete(reverse('saved_posts_api_toggle', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)

    def test_devuelve_404_si_el_post_no_existe(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(reverse('saved_posts_api_toggle', args=[999999]))
        self.assertEqual(response.status_code, 404)