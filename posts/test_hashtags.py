from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from .models import Hashtag, Post, PostHashtag


class HashtagDetailVisibilidadTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('hash_autor', password='x')
        self.avanzado = User.objects.create_user('hash_avanzado', password='x')
        self.atrasado = User.objects.create_user('hash_atrasado', password='x')

        self.obra = Obra.objects.create(titulo='Serie Hashtag', slug='serie-hashtag')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.e3 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E3', orden_local=3)
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e3.refresh_from_db()

        actualizar_progreso(self.avanzado, self.obra, self.e3)
        actualizar_progreso(self.atrasado, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='el villano muere',
            referencia_narrativa=self.e1, frontera_spoiler=self.e3,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        hashtag = Hashtag.objects.create(name='plottwist')
        PostHashtag.objects.create(post=self.post, hashtag=hashtag)
        self.url = reverse('hashtag_detail', args=['plottwist'])

    def _ids_listados(self, response):
        return [p.id for p in response.context['posts']]

    def test_usuario_atrasado_no_ve_el_spoiler_en_el_hashtag(self):
        self.client.force_login(self.atrasado)
        response = self.client.get(self.url)
        self.assertEqual(self._ids_listados(response), [])

    def test_usuario_avanzado_ve_el_post_en_el_hashtag(self):
        self.client.force_login(self.avanzado)
        response = self.client.get(self.url)
        self.assertEqual(self._ids_listados(response), [self.post.id])

    def test_anonimo_no_ve_posts_en_el_hashtag(self):
        response = self.client.get(self.url)
        self.assertEqual(self._ids_listados(response), [])