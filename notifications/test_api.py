from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Notification


class NotificationListAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('notif_receiver', password='x')
        self.actor = User.objects.create_user('notif_actor', password='x')

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('notifications_api_list'))
        self.assertEqual(response.status_code, 403)

    def test_lista_solo_las_notificaciones_del_usuario(self):
        Notification.objects.create(
            actor=self.actor, user=self.usuario, verb='te ha seguido', target_type='follow',
        )
        otro_usuario = User.objects.create_user('otro_notif', password='x')
        Notification.objects.create(
            actor=self.actor, user=otro_usuario, verb='te ha seguido', target_type='follow',
        )

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('notifications_api_list'))
        self.assertEqual(len(response.data['results']), 1)

    def test_marca_como_vistas_al_cargar_sin_parametro_de_pagina(self):
        Notification.objects.create(
            actor=self.actor, user=self.usuario, verb='te ha seguido',
            target_type='follow', seen=False,
        )

        self.client.force_authenticate(user=self.usuario)
        self.client.get(reverse('notifications_api_list'))

        self.assertFalse(Notification.objects.filter(user=self.usuario, seen=False).exists())

    def test_marca_como_vistas_al_cargar_pagina_1_explicita(self):
        Notification.objects.create(
            actor=self.actor, user=self.usuario, verb='te ha seguido',
            target_type='follow', seen=False,
        )

        self.client.force_authenticate(user=self.usuario)
        self.client.get(reverse('notifications_api_list'), {'page': '1'})

        self.assertFalse(Notification.objects.filter(user=self.usuario, seen=False).exists())

    def test_no_marca_como_vistas_al_cargar_pagina_2(self):
        Notification.objects.create(
            actor=self.actor, user=self.usuario, verb='te ha seguido',
            target_type='follow', seen=False,
        )

        self.client.force_authenticate(user=self.usuario)
        self.client.get(reverse('notifications_api_list'), {'page': '2'})

        self.assertTrue(Notification.objects.filter(user=self.usuario, seen=False).exists())

    def test_incluye_avatar_y_url_calculados(self):
        notif = Notification.objects.create(
            actor=self.actor, user=self.usuario, verb='te ha seguido', target_type='follow',
        )

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('notifications_api_list'))
        data = response.data['results'][0]
        self.assertEqual(data['id'], notif.id)
        self.assertIn('avatar', data)
        self.assertEqual(data['url'], f'/perfil/{self.actor.username}/react/')

    def test_paginacion_has_next(self):
        for i in range(16):
            Notification.objects.create(
                actor=self.actor, user=self.usuario, verb=f'accion {i}', target_type='follow',
            )

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('notifications_api_list'))
        self.assertEqual(len(response.data['results']), 15)
        self.assertTrue(response.data['has_next'])

        response_pagina_2 = self.client.get(reverse('notifications_api_list'), {'page': '2'})
        self.assertEqual(len(response_pagina_2.data['results']), 1)
        self.assertFalse(response_pagina_2.data['has_next'])