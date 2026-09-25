from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from follows.models import Follow
from .models import Hashtag


class MentionsSearchTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('autocompletar', password='x')
        User.objects.create_user('autocompletar_otro', password='x')

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('mentions_search'), {'q': 'auto'})
        self.assertEqual(response.status_code, 302)

    def test_devuelve_coincidencias_por_prefijo(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('mentions_search'), {'q': 'autocompletar'})
        usernames = [r['username'] for r in response.json()['results']]
        self.assertIn('autocompletar_otro', usernames)

    def test_sin_query_no_devuelve_resultados(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('mentions_search'))
        self.assertEqual(response.json()['results'], [])

    def test_no_incluye_al_propio_usuario(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('mentions_search'), {'q': 'autocompletar'})
        usernames = [r['username'] for r in response.json()['results']]
        self.assertNotIn('autocompletar', usernames)

    def test_prioriza_usuarios_seguidos(self):
        seguido = User.objects.create_user('menc_ana_seguida', password='x')
        User.objects.create_user('menc_ana_no_relacionada', password='x')
        Follow.objects.create(follower=self.usuario, followed=seguido)

        self.client.force_login(self.usuario)
        response = self.client.get(reverse('mentions_search'), {'q': 'menc_ana'})
        usernames = [r['username'] for r in response.json()['results']]
        self.assertEqual(usernames[0], 'menc_ana_seguida')

    def test_prioriza_usuarios_que_te_siguen(self):
        seguidor = User.objects.create_user('menc_bob_seguidor', password='x')
        User.objects.create_user('menc_bob_no_relacionado', password='x')
        Follow.objects.create(follower=seguidor, followed=self.usuario)

        self.client.force_login(self.usuario)
        response = self.client.get(reverse('mentions_search'), {'q': 'menc_bob'})
        usernames = [r['username'] for r in response.json()['results']]
        self.assertEqual(usernames[0], 'menc_bob_seguidor')

    def test_sin_relaciones_mantiene_orden_alfabetico(self):
        User.objects.create_user('menc_zeta', password='x')
        User.objects.create_user('menc_alfa', password='x')

        self.client.force_login(self.usuario)
        response = self.client.get(reverse('mentions_search'), {'q': 'menc_'})
        usernames = [r['username'] for r in response.json()['results']]
        self.assertEqual(usernames, ['menc_alfa', 'menc_zeta'])


class HashtagsSearchTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('hashtag_user', password='x')
        Hashtag.objects.create(name='revealless')
        Hashtag.objects.create(name='reveal')

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('hashtags_search'), {'q': 'rev'})
        self.assertEqual(response.status_code, 302)

    def test_devuelve_coincidencias_por_prefijo(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('hashtags_search'), {'q': 'rev'})
        names = [r['name'] for r in response.json()['results']]
        self.assertEqual(set(names), {'revealless', 'reveal'})


class SuggestedHashtagsTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('sugeridos_user', password='x')

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('suggested_hashtags'))
        self.assertEqual(response.status_code, 302)

    def test_responde_200_autenticado(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('suggested_hashtags'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.json())