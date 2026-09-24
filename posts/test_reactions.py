from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from likes.models import PostReaction
from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from .models import Post


class ReaccionesPostVisibilidadTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('reac_autor', password='x')
        self.lector = User.objects.create_user('reac_lector', password='x')

        self.obra = Obra.objects.create(titulo='Serie Reacciones', slug='serie-reacciones')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.e3 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E3', orden_local=3)
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e3.refresh_from_db()
        actualizar_progreso(self.lector, self.obra, self.e1)

        self.post_visible = Post.objects.create(
            author=self.autor, obra=self.obra, text='post visible',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.post_oculto = Post.objects.create(
            author=self.autor, obra=self.obra, text='post oculto',
            referencia_narrativa=self.e1, frontera_spoiler=self.e3,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.client.force_login(self.lector)

    def test_no_se_puede_reaccionar_a_un_post_oculto(self):
        response = self.client.post(
            reverse('toggle_reaction_post'),
            {'post_id': self.post_oculto.id, 'reaction': 'me_gusta'},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(PostReaction.objects.filter(post=self.post_oculto).exists())

    def test_se_puede_reaccionar_a_un_post_visible(self):
        response = self.client.post(
            reverse('toggle_reaction_post'),
            {'post_id': self.post_visible.id, 'reaction': 'me_gusta'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PostReaction.objects.filter(post=self.post_visible).exists())

    def test_no_se_pueden_listar_reacciones_de_un_post_oculto(self):
        response = self.client.get(reverse('post_reactions_list', args=[self.post_oculto.id]))
        self.assertEqual(response.status_code, 404)

    def test_se_pueden_listar_reacciones_de_un_post_visible(self):
        response = self.client.get(reverse('post_reactions_list', args=[self.post_visible.id]))
        self.assertEqual(response.status_code, 200)