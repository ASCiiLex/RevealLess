from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class PanelAdminTests(TestCase):
    def test_el_inicio_del_admin_carga_con_sus_metricas(self):
        # Recorre dashboard_callback, los componentes de gráficos y los contadores del menú.
        admin = User.objects.create_superuser('admin_panel', 'admin@example.com', 'x')
        self.client.force_login(admin)
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('actividad_por_obra', response.context)