from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from follows.models import Follow
from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from posts.models import Post


class ProfileDetailAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('perfil_viewer', password='x')
        self.dueño = User.objects.create_user('perfil_dueño', password='x')
        self.dueño.profile.bio = 'Mi biografía'
        self.dueño.profile.save()

        Follow.objects.create(follower=self.usuario, followed=self.dueño)

        self.obra = Obra.objects.create(titulo='Serie Perfil', slug='serie-perfil')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()

        actualizar_progreso(self.usuario, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.dueño, obra=self.obra, text='post visible',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_no_requiere_autenticacion(self):
        response = self.client.get(reverse('profiles_api_detail', args=['perfil_dueño']))
        self.assertEqual(response.status_code, 200)

    def test_devuelve_404_si_usuario_no_existe(self):
        response = self.client.get(reverse('profiles_api_detail', args=['no_existe']))
        self.assertEqual(response.status_code, 404)

    def test_incluye_bio_y_username(self):
        response = self.client.get(reverse('profiles_api_detail', args=['perfil_dueño']))
        self.assertEqual(response.data['username'], 'perfil_dueño')
        self.assertEqual(response.data['bio'], 'Mi biografía')

    def test_is_following_true_si_el_usuario_autenticado_sigue_al_perfil(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('profiles_api_detail', args=['perfil_dueño']))
        self.assertTrue(response.data['is_following'])

    def test_is_following_false_para_anonimo(self):
        response = self.client.get(reverse('profiles_api_detail', args=['perfil_dueño']))
        self.assertFalse(response.data['is_following'])

    def test_is_own_profile_true_para_el_propio_dueño(self):
        self.client.force_authenticate(user=self.dueño)
        response = self.client.get(reverse('profiles_api_detail', args=['perfil_dueño']))
        self.assertTrue(response.data['is_own_profile'])

    def test_contadores_de_followers_y_following(self):
        response = self.client.get(reverse('profiles_api_detail', args=['perfil_dueño']))
        self.assertEqual(response.data['followers_count'], 1)
        self.assertEqual(response.data['following_count'], 0)

    def test_posts_respetan_visible_for(self):
        """Un post con frontera de spoiler adelantada respecto al
        progreso del visitante no debe aparecer en su grid de perfil."""
        e2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.obra.recalcular_orden()
        e2.refresh_from_db()

        post_bloqueado = Post.objects.create(
            author=self.dueño, obra=self.obra, text='post con spoiler',
            referencia_narrativa=self.e1, frontera_spoiler=e2,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('profiles_api_detail', args=['perfil_dueño']))
        ids = [p['id'] for p in response.data['posts']]
        self.assertIn(self.post.id, ids)
        self.assertNotIn(post_bloqueado.id, ids)


class ProfileEditAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user(
            'editor_perfil', email='editor@example.com', password='x',
        )
        self.otro_usuario = User.objects.create_user(
            'otro_editor', email='otro@example.com', password='x',
        )

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('profiles_api_edit'))
        self.assertEqual(response.status_code, 403)

    def test_get_devuelve_datos_actuales(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('profiles_api_edit'))
        self.assertEqual(response.data['username'], 'editor_perfil')
        self.assertEqual(response.data['email'], 'editor@example.com')

    def test_patch_actualiza_bio(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.patch(
            reverse('profiles_api_edit'),
            {'username': 'editor_perfil', 'email': 'editor@example.com', 'bio': 'Nueva bio'},
        )
        self.assertEqual(response.status_code, 200)
        self.usuario.profile.refresh_from_db()
        self.assertEqual(self.usuario.profile.bio, 'Nueva bio')

    def test_patch_rechaza_username_duplicado(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.patch(
            reverse('profiles_api_edit'),
            {'username': 'otro_editor', 'email': 'editor@example.com'},
        )
        self.assertEqual(response.status_code, 400)

    def test_patch_rechaza_email_duplicado(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.patch(
            reverse('profiles_api_edit'),
            {'username': 'editor_perfil', 'email': 'otro@example.com'},
        )
        self.assertEqual(response.status_code, 400)

    def test_patch_permite_mantener_el_propio_username(self):
        """No debe rechazarse por 'duplicado' el propio username/email
        del usuario que edita -- exclude(pk=user.pk) debe cubrir esto."""
        self.client.force_authenticate(user=self.usuario)
        response = self.client.patch(
            reverse('profiles_api_edit'),
            {'username': 'editor_perfil', 'email': 'editor@example.com', 'bio': 'Sin cambios de identidad'},
        )
        self.assertEqual(response.status_code, 200)