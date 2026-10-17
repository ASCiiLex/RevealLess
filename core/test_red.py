from django.test import RequestFactory, SimpleTestCase

from core.red import ip_cliente


class IpClienteTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_usa_true_client_ip(self):
        request = self.factory.get('/', HTTP_TRUE_CLIENT_IP='203.0.113.7', HTTP_X_FORWARDED_FOR='1.1.1.1')
        self.assertEqual(ip_cliente(request), '203.0.113.7')

    def test_usa_cf_connecting_ip_si_no_hay_true_client_ip(self):
        request = self.factory.get('/', HTTP_CF_CONNECTING_IP='2001:db8::1')
        self.assertEqual(ip_cliente(request), '2001:db8::1')

    def test_ignora_x_forwarded_for(self):
        request = self.factory.get('/', HTTP_X_FORWARDED_FOR='1.1.1.1')
        self.assertEqual(ip_cliente(request), '127.0.0.1')

    def test_valor_invalido_cae_a_remote_addr(self):
        request = self.factory.get('/', HTTP_TRUE_CLIENT_IP='no-es-una-ip')
        self.assertEqual(ip_cliente(request), '127.0.0.1')