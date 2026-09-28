from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra


def crear_obras(n, prefijo='Obra'):
    return [Obra.objects.create(titulo=f'{prefijo} {i:02d}', slug=f'{prefijo.lower()}-{i}') for i in range(n)]


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

    def test_landing_sin_cabecera_ni_barra_inferior(self):
        # Logo y acceso viven en el hero.
        response = self.client.get(reverse('feed_publico'))
        self.assertNotContains(response, '<header class="pl-header">')
        self.assertNotContains(response, 'class="pl-bottom-nav"')

    def test_hero_monta_el_login_con_cookie_csrf(self):
        response = self.client.get(reverse('feed_publico'))
        self.assertContains(response, 'id="hero-login"')
        self.assertIn('csrftoken', response.cookies)

    def test_landing_limita_el_adelanto_a_seis_obras(self):
        crear_obras(7)
        response = self.client.get(reverse('feed_publico'))
        self.assertEqual(len(response.context['obras']), 6)
        self.assertEqual(response.context['stats']['obras_count'], 8)

    def test_landing_tiene_footer(self):
        response = self.client.get(reverse('feed_publico'))
        self.assertContains(response, '<footer class="pl-footer">')

    def test_footer_tiene_logo(self):
        response = self.client.get(reverse('feed_publico'))
        self.assertContains(response, 'pl-footer-logo')

    def test_footer_enlaza_al_catalogo(self):
        response = self.client.get(reverse('feed_publico'))
        self.assertContains(response, f'href="{reverse("catalogo_publico")}"')

    def test_usuario_autenticado_va_al_feed_react(self):
        self.client.force_login(User.objects.create_user('landing_user', password='x'))
        response = self.client.get(reverse('feed_publico'))
        self.assertRedirects(response, reverse('feed'), fetch_redirect_response=False)


class CatalogoPublicoTests(TestCase):
    def test_catalogo_muestra_la_primera_tanda(self):
        crear_obras(14)
        response = self.client.get(reverse('catalogo_publico'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_obras'], 14)
        self.assertEqual(len(response.context['pagina']), 12)
        self.assertTrue(response.context['pagina'].has_next())

    def test_catalogo_tiene_cabecera_y_barra_inferior(self):
        response = self.client.get(reverse('catalogo_publico'))
        self.assertContains(response, '<header class="pl-header">')
        self.assertContains(response, 'class="pl-bottom-nav"')

    def test_sinopsis_es_colapsable(self):
        crear_obras(1)
        response = self.client.get(reverse('catalogo_publico'))
        self.assertContains(response, '<details class="pl-sinopsis"')

    def test_catalogo_parcial_devuelve_solo_tarjetas_y_la_pagina_siguiente(self):
        crear_obras(14)
        response = self.client.get(reverse('catalogo_publico'), {'pagina': 2, 'parcial': 1})
        self.assertEqual([t.name for t in response.templates], ['feed/_catalogo_tarjetas.html'])
        self.assertEqual(len(response.context['pagina']), 2)
        self.assertEqual(response['X-Pagina-Siguiente'], '')

    def test_catalogo_parcial_indica_la_siguiente_si_quedan_obras(self):
        crear_obras(30)
        response = self.client.get(reverse('catalogo_publico'), {'pagina': 1, 'parcial': 1})
        self.assertEqual(response['X-Pagina-Siguiente'], '2')

    def test_catalogo_pagina_no_numerica_cae_en_la_primera(self):
        crear_obras(3)
        response = self.client.get(reverse('catalogo_publico'), {'pagina': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pagina'].number, 1)


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
        self.assertContains(response, 'href="/notificaciones/"')

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


class FeedReactLegacyRedirectTests(TestCase):
    """/feed/react/ ya no es una ruta propia; comprueba que redirige
    en vez de dar 404, por si queda marcada en favoritos o en enlaces
    compartidos de antes de la limpieza de rutas."""

    def test_visitante_va_a_la_landing(self):
        response = self.client.get('/feed/react/')
        self.assertRedirects(response, reverse('feed_publico'), fetch_redirect_response=False)

    def test_autenticado_va_al_feed_real(self):
        self.client.force_login(User.objects.create_user('legacy_feed_user', password='x'))
        response = self.client.get('/feed/react/')
        self.assertRedirects(response, reverse('feed'), fetch_redirect_response=False)