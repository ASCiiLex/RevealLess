from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Obra, UnidadNarrativa, ProgresoUsuario


class SeleccionarObraViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('selector', password='x')
        self.obra = Obra.objects.create(titulo='Serie Select', slug='serie-select')
        self.unidad = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.unidad.refresh_from_db()
        self.client.force_login(self.user)

    def test_requiere_autenticacion(self):
        self.client.logout()
        response = self.client.get(reverse('narrative_seleccionar_obra'))
        self.assertEqual(response.status_code, 302)

    def test_sin_progreso_redirige_a_declarar_progreso_con_next(self):
        response = self.client.post(reverse('narrative_seleccionar_obra'), {'obra': self.obra.id})
        esperado = reverse('narrative_declarar_progreso', kwargs={'obra_slug': self.obra.slug})
        create_url = reverse('create_post', kwargs={'obra_slug': self.obra.slug})
        self.assertRedirects(response, f'{esperado}?next={create_url}')

    def test_con_progreso_redirige_directo_a_crear_post(self):
        ProgresoUsuario.objects.create(
            usuario=self.user, obra=self.obra, unidad_actual=self.unidad,
            orden_absoluto=self.unidad.orden_inicio,
        )
        response = self.client.post(reverse('narrative_seleccionar_obra'), {'obra': self.obra.id})
        self.assertRedirects(response, reverse('create_post', kwargs={'obra_slug': self.obra.slug}))


class DeclararProgresoViewTests(TestCase):
    """Foco principal: la protección anti open-redirect en next_url.
    Sin este test, alguien podría romper url_has_allowed_host_and_scheme
    en un refactor futuro sin que nada lo detecte."""

    def setUp(self):
        self.user = User.objects.create_user('declarante', password='x')
        self.obra = Obra.objects.create(titulo='Serie Progreso', slug='serie-progreso')
        self.unidad = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.unidad.refresh_from_db()
        self.client.force_login(self.user)
        self.url = reverse('narrative_declarar_progreso', kwargs={'obra_slug': self.obra.slug})

    def test_requiere_autenticacion(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_devuelve_404_si_la_obra_no_existe(self):
        url = reverse('narrative_declarar_progreso', kwargs={'obra_slug': 'no-existe'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_next_url_externa_maliciosa_se_descarta(self):
        """El caso central: un next apuntando a otro dominio no debe
        usarse jamás como destino de redirect, caiga a /feed/."""
        response = self.client.get(f'{self.url}?next=https://sitio-malicioso.com/robar-sesion')
        self.assertEqual(response.context['next'], reverse('feed'))

    def test_next_url_con_protocolo_relativo_se_descarta(self):
        """//evil.com es una URL relativa de esquema que el navegador
        interpreta como externa — variante clásica de bypass que
        url_has_allowed_host_and_scheme debe rechazar igual."""
        response = self.client.get(f'{self.url}?next=//evil.com/phishing')
        self.assertEqual(response.context['next'], reverse('feed'))

    def test_next_url_interna_valida_se_conserva(self):
        create_url = reverse('create_post', kwargs={'obra_slug': self.obra.slug})
        response = self.client.get(f'{self.url}?next={create_url}')
        self.assertEqual(response.context['next'], create_url)

    def test_sin_next_url_cae_a_feed_por_defecto(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['next'], reverse('feed'))

    def test_declarar_progreso_redirige_a_next_al_guardar(self):
        create_url = reverse('create_post', kwargs={'obra_slug': self.obra.slug})
        response = self.client.post(
            f'{self.url}?next={create_url}',
            {'unidad_actual': self.unidad.id},
        )
        self.assertRedirects(response, create_url, fetch_redirect_response=False)

    def test_next_maliciosa_no_sobrevive_ni_siquiera_tras_guardar_progreso(self):
        """Refuerzo del caso central: aunque el formulario se envíe
        (POST) con una next maliciosa, el redirect final tampoco debe
        acabar ahí."""
        response = self.client.post(
            f'{self.url}?next=https://sitio-malicioso.com/robar-sesion',
            {'unidad_actual': self.unidad.id},
        )
        self.assertRedirects(response, reverse('feed'), fetch_redirect_response=False)


class ObraReactViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('react_user', password='x')
        self.obra = Obra.objects.create(titulo='Serie React', slug='serie-react')
        self.client.force_login(self.user)

    def test_progreso_react_devuelve_404_si_obra_no_existe(self):
        url = reverse('narrative_progreso_react', kwargs={'obra_slug': 'no-existe'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_progreso_react_ok_si_obra_existe(self):
        url = reverse('narrative_progreso_react', kwargs={'obra_slug': self.obra.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_obra_landing_react_devuelve_404_si_obra_no_existe(self):
        url = reverse('narrative_obra_landing_react', kwargs={'obra_slug': 'no-existe'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_obra_temas_react_devuelve_404_si_obra_no_existe(self):
        url = reverse('narrative_obra_temas_react', kwargs={'obra_slug': 'no-existe'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)