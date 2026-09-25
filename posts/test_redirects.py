from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from .models import Post


class PostDetailRedirectTests(TestCase):
    def test_post_detail_redirige_a_react(self):
        autor = User.objects.create_user('redir_post_autor', password='x')
        obra = Obra.objects.create(titulo='Serie Redirect', slug='serie-redirect')
        e1 = UnidadNarrativa.objects.create(obra=obra, tipo='episodio', nombre='E1', orden_local=1)
        obra.recalcular_orden()
        e1.refresh_from_db()

        post = Post.objects.create(
            author=autor, obra=obra, text='post redirect',
            referencia_narrativa=e1, frontera_spoiler=e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

        response = self.client.get(reverse('post_detail', args=[post.id]))
        self.assertRedirects(
            response, f'/posts/{post.id}/react/', fetch_redirect_response=False
        )