import os
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import ProgresoUsuario, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from ..models import Post
from .utils import crear_obra


class PostCreateAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('publicador', password='x')
        self.obra, self.ep = crear_obra('serie-publicar', 7)
        self.url = reverse('posts_api_create', args=[self.obra.slug])

    def _con_progreso(self, unidad=None):
        actualizar_progreso(self.usuario, self.obra, unidad or self.ep[0])
        self.client.force_authenticate(user=self.usuario)

    def _publicar(self, text, **extra):
        return self.client.post(self.url, {'text': text, 'referencia_narrativa': self.ep[0].id, **extra})

    def _progreso_actual(self):
        return ProgresoUsuario.objects.get(usuario=self.usuario, obra=self.obra).unidad_actual

    def test_requiere_autenticacion(self):
        self.assertEqual(self._publicar('hola').status_code, 403)

    def test_sin_progreso_previo_devuelve_409(self):
        self.client.force_authenticate(user=self.usuario)
        response = self._publicar('hola')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['detail'], 'progreso_requerido')

    def test_crea_post_con_frontera_explicita(self):
        self._con_progreso()
        self.assertEqual(self._publicar('explicita', frontera_spoiler=self.ep[1].id).status_code, 201)

        post = Post.objects.get(text='explicita')
        self.assertEqual(post.frontera_origen, ClasificacionNarrativa.ORIGEN_EXPLICITO)
        self.assertEqual(post.frontera_spoiler, self.ep[1])

    # Sin clave explícita en el test: nunca debe depender del .env ni llamar a la API real.
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': ''})
    def test_sin_frontera_explicita_cae_a_fallback_sin_api_key(self):
        self._con_progreso()
        self.assertEqual(self._publicar('fallback').status_code, 201)

        post = Post.objects.get(text='fallback')
        self.assertEqual(post.frontera_origen, ClasificacionNarrativa.ORIGEN_FALLBACK)
        self.assertEqual(post.frontera_spoiler, self.ep[0])

    def test_actualiza_progreso_desde_el_formulario(self):
        self._con_progreso()
        self._publicar('avanzando', frontera_spoiler=self.ep[1].id, nuevo_progreso=self.ep[1].id)
        self.assertEqual(self._progreso_actual(), self.ep[1])

    def test_nuevo_progreso_anterior_al_actual_devuelve_400(self):
        self._con_progreso()
        actualizar_progreso(self.usuario, self.obra, self.ep[1])

        response = self._publicar('retroceso', nuevo_progreso=self.ep[0].id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._progreso_actual(), self.ep[1])

    def test_salto_grande_de_progreso_devuelve_409(self):
        self._con_progreso()
        response = self._publicar('salto', frontera_spoiler=self.ep[-1].id, nuevo_progreso=self.ep[-1].id)
        self.assertEqual(response.status_code, 409)
        self.assertTrue(response.data['requiere_confirmacion_progreso'])

    def test_salto_grande_confirmado_se_aplica(self):
        self._con_progreso()
        response = self._publicar(
            'salto confirmado', frontera_spoiler=self.ep[-1].id, nuevo_progreso=self.ep[-1].id,
            confirmar_salto_progreso='true',
        )
        self.assertEqual(response.status_code, 201)

    def test_rechaza_texto_vacio(self):
        self._con_progreso()
        self.assertEqual(self._publicar('').status_code, 400)

    def test_crea_post_con_emocion_autor(self):
        self._con_progreso()
        response = self._publicar('con emocion', emocion_autor='me_encanta')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['emocion_autor'], 'me_encanta')

    def test_post_sin_emocion_autor_queda_null(self):
        self._con_progreso()
        response = self._publicar('sin emocion')
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data['emocion_autor'])

    def test_rechaza_emocion_autor_invalida(self):
        self._con_progreso()
        self.assertEqual(self._publicar('invalida', emocion_autor='no_existe').status_code, 400)