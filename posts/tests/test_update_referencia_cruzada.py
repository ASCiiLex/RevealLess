from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra
from .utils import crear_obra, crear_post


class EdicionReferenciaCruzadaTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        autor = User.objects.create_user('editor_cruzado', password='x')
        anime, (e1,) = crear_obra('anime-edicion')
        self.manga, (self.cap,) = crear_obra('manga-edicion', tipo_unidad='capitulo', tipo=Obra.TIPO_MANGA)
        self.post = crear_post(autor, anime, e1)

        self.client.force_authenticate(user=autor)
        self.url = reverse('posts_api_update', args=[self.post.id])

    def _editar(self, **datos):
        return self.client.patch(self.url, datos, format='multipart')

    def test_rechaza_obra_cruzada_sin_frontera(self):
        self.assertEqual(self._editar(obra_cruzada=self.manga.id).status_code, 400)
        self.post.refresh_from_db()
        self.assertIsNone(self.post.obra_cruzada)

    def test_acepta_obra_y_frontera_cruzadas_juntas(self):
        response = self._editar(obra_cruzada=self.manga.id, frontera_cruzada=self.cap.id)
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.obra_cruzada, self.manga)

    def test_quitar_obra_cruzada_con_valores_vacios(self):
        self.post.obra_cruzada = self.manga
        self.post.frontera_cruzada = self.cap
        self.post.save()

        self.assertEqual(self._editar(obra_cruzada='', frontera_cruzada='').status_code, 200)

        self.post.refresh_from_db()
        self.assertIsNone(self.post.obra_cruzada)
        self.assertIsNone(self.post.frontera_cruzada)
        self.assertIsNone(self.post.frontera_cruzada_orden)