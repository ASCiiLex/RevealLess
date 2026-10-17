from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings

from posts.api_views.crear import _ia_disponible


class LimiteIAPublicarTests(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()

    def _peticion(self, username):
        request = self.factory.post('/')
        request.user = User.objects.create_user(username, password='clave-de-prueba')
        return request

    @override_settings(IA_LIMITE_PUBLICAR='2/h')
    def test_superado_el_limite_deja_de_consultar_la_ia(self):
        request = self._peticion('lector')
        self.assertEqual([_ia_disponible(request) for _ in range(3)], [True, True, False])

    @override_settings(IA_LIMITE_PUBLICAR='1/h')
    def test_el_limite_es_por_usuario(self):
        self.assertTrue(_ia_disponible(self._peticion('uno')))
        self.assertTrue(_ia_disponible(self._peticion('otro')))