from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, ProgresoUsuario
from narrative.services import actualizar_progreso
from ..models import Post
from .utils import crear_obra

TEXTO = 'esto pasó en el manga'


class ReferenciaCruzadaEnPostCreateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('publicador_cruzado', password='x')

        self.anime, (self.e1, self.e2) = crear_obra('anime-x', 2, tipo=Obra.TIPO_SERIE)
        self.manga, (self.cap,) = crear_obra(
            'manga-x', tipo_unidad='capitulo', tipo=Obra.TIPO_MANGA, adapta_a=self.anime,
        )

        actualizar_progreso(self.usuario, self.anime, self.e1)
        self.client.force_authenticate(user=self.usuario)
        self.url = reverse('posts_api_create', args=[self.anime.slug])

    def _publicar(self, text=TEXTO, **extra):
        return self.client.post(self.url, {'text': text, 'referencia_narrativa': self.e1.id, **extra})

    def test_deteccion_bloquea_y_devuelve_detecciones(self):
        response = self._publicar()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['detail'], 'referencia_cruzada_detectada')
        self.assertEqual(response.data['detecciones'][0]['obra_slug'], self.manga.slug)
        self.assertFalse(Post.objects.filter(text=TEXTO).exists())

    def test_deteccion_no_avanza_el_progreso(self):
        """Regresión: el progreso se actualizaba antes del 409 de detección."""
        self.assertEqual(self._publicar(nuevo_progreso=self.e2.id).status_code, 409)
        progreso = ProgresoUsuario.objects.get(usuario=self.usuario, obra=self.anime)
        self.assertEqual(progreso.unidad_actual, self.e1)

    def test_confirmar_referencia_cruzada_publica_con_ambos_campos(self):
        response = self._publicar(obra_cruzada=self.manga.id, frontera_cruzada=self.cap.id)
        self.assertEqual(response.status_code, 201)
        post = Post.objects.get(text=TEXTO)
        self.assertEqual(post.obra_cruzada, self.manga)
        self.assertEqual(post.frontera_cruzada, self.cap)

    def test_descartar_referencia_cruzada_publica_sin_marcar(self):
        self.assertEqual(self._publicar(descartar_referencia_cruzada='true').status_code, 201)
        self.assertIsNone(Post.objects.get(text=TEXTO).obra_cruzada)

    def test_texto_sin_palabra_clave_no_activa_deteccion(self):
        self.assertEqual(self._publicar('un texto normal sin nada especial').status_code, 201)