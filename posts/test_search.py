from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from .models import Post


class GlobalSearchVisibilidadTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('busq_autor', password='x')
        self.avanzado = User.objects.create_user('busq_avanzado', password='x')
        self.atrasado = User.objects.create_user('busq_atrasado', password='x')

        self.obra = Obra.objects.create(titulo='Serie Busqueda', slug='serie-busqueda')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.e3 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E3', orden_local=3)
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e3.refresh_from_db()

        actualizar_progreso(self.avanzado, self.obra, self.e3)
        actualizar_progreso(self.atrasado, self.obra, self.e1)

        Post.objects.create(
            author=self.autor, obra=self.obra, text='el villano muere',
            referencia_narrativa=self.e1, frontera_spoiler=self.e3,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.url = reverse('global_search')

    def test_usuario_atrasado_no_ve_el_spoiler_en_la_busqueda(self):
        self.client.force_login(self.atrasado)
        response = self.client.get(self.url, {'q': 'villano'})
        self.assertEqual(response.json()['posts'], [])

    def test_usuario_avanzado_ve_el_post_en_la_busqueda(self):
        self.client.force_login(self.avanzado)
        response = self.client.get(self.url, {'q': 'villano'})
        self.assertEqual(len(response.json()['posts']), 1)

    def test_anonimo_no_ve_posts_en_la_busqueda(self):
        response = self.client.get(self.url, {'q': 'villano'})
        self.assertEqual(response.json()['posts'], [])