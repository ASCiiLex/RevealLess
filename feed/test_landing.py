from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra


class LandingPublicaTests(TestCase):
    def setUp(self):
        Obra.objects.create(titulo='Obra Landing', slug='obra-landing')

    def test_visitante_ve_la_landing(self):
        response = self.client.get(reverse('feed_publico'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'feed/public_landing.html')
        self.assertContains(response, 'Obra Landing')

    def test_landing_enlaza_a_login_y_registro_react(self):
        response = self.client.get(reverse('feed_publico'))
        self.assertContains(response, 'href="/cuentas/login/"')
        self.assertContains(response, 'href="/cuentas/register/"')

    def test_landing_no_enlaza_a_vistas_clasicas(self):
        response = self.client.get(reverse('feed_publico'))
        self.assertNotContains(response, 'href="/cuentas/login/legacy/"')

    def test_sinopsis_es_colapsable(self):
        response = self.client.get(reverse('feed_publico'))
        self.assertContains(response, '<details>')

    def test_landing_tiene_footer(self):
        response = self.client.get(reverse('feed_publico'))
        self.assertContains(response, '<footer class="pl-footer">')

    def test_footer_tiene_logo(self):
        response = self.client.get(reverse('feed_publico'))
        self.assertContains(response, 'pl-footer-logo')

    def test_footer_enlaza_al_catalogo(self):
        response = self.client.get(reverse('feed_publico'))
        self.assertContains(response, 'href="#catalogo"')
        self.assertContains(response, 'id="catalogo"')

    def test_landing_tiene_barra_inferior_de_acceso(self):
        response = self.client.get(reverse('feed_publico'))
        self.assertContains(response, 'class="pl-bottom-nav"')

    def test_usuario_autenticado_va_al_feed_react(self):
        self.client.force_login(User.objects.create_user('landing_user', password='x'))
        response = self.client.get(reverse('feed_publico'))
        self.assertRedirects(response, reverse('feed'), fetch_redirect_response=False)


class RedireccionesHaciaVistasReactTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('redir_user', password='x')

    def test_raiz_visitante_va_a_la_landing(self):
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, reverse('feed_publico'), fetch_redirect_response=False)

    def test_raiz_autenticado_va_al_feed_react(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, reverse('feed'), fetch_redirect_response=False)

    def test_login_autenticado_va_al_feed_react(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('feed'), fetch_redirect_response=False)

    def test_register_autenticado_va_al_feed_react(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, reverse('feed'), fetch_redirect_response=False)

    def test_post_no_existe_enlaza_a_notificaciones_react(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('post_not_found', args=[1]))
        self.assertContains(response, 'href="/notificaciones/react/"')

    def test_post_no_existe_no_muestra_botones_de_acceso(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('post_not_found', args=[1]))
        self.assertNotContains(response, 'href="/cuentas/login/"')
        self.assertNotContains(response, 'class="pl-bottom-nav"')

    def test_post_no_existe_footer_sin_enlaces_de_acceso(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('post_not_found', args=[1]))
        self.assertContains(response, '<footer class="pl-footer">')
        self.assertNotContains(response, 'pl-footer-links')