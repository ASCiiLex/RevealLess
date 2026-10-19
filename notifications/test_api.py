from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient

from comments.models import Comment
from narrative.models import ClasificacionNarrativa, Obra, UnidadNarrativa
from posts.models import Post
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
        self.assertEqual(data['url'], f'/perfil/{self.actor.username}/')

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


class NotificationConsultasTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('notif_consultas', password='x')
        obra = Obra.objects.create(titulo='Serie Notificaciones', slug='serie-notificaciones')
        e1 = UnidadNarrativa.objects.create(obra=obra, tipo='episodio', nombre='E1', orden_local=1)
        obra.recalcular_orden()
        e1.refresh_from_db()
        self.post = Post.objects.create(
            author=self.usuario, obra=obra, text='post',
            referencia_narrativa=e1, frontera_spoiler=e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.comentario = Comment.objects.create(
            user=self.usuario, post=self.post, text='comentario', referencia_narrativa=e1,
        )
        self.client.force_authenticate(user=self.usuario)

    def _crear(self, cuantas):
        for i in range(cuantas):
            actor = User.objects.create_user(f'notif_actor_{Notification.objects.count()}_{i}', password='x')
            Notification.objects.create(actor=actor, user=self.usuario, verb='reacted', target_type='post', target_id=self.post.id)
            Notification.objects.create(
                actor=actor, user=self.usuario, verb='replied', target_type='reply', target_id=self.comentario.id,
            )
            Notification.objects.create(actor=actor, user=self.usuario, verb='te ha seguido', target_type='follow')

    def _consultas(self):
        with CaptureQueriesContext(connection) as consultas:
            self.client.get(reverse('notifications_api_list'))
        return len(consultas)

    def test_las_consultas_no_crecen_con_las_notificaciones(self):
        self._crear(1)
        antes = self._consultas()
        self._crear(3)
        self.assertEqual(self._consultas(), antes)

    def test_las_de_comentario_apuntan_a_su_post(self):
        self._crear(1)
        resultados = self.client.get(reverse('notifications_api_list')).data['results']
        respuesta = next(r for r in resultados if r['verb'] == 'respondió a tu comentario')
        self.assertEqual(respuesta['url'], f'/posts/{self.post.id}/')