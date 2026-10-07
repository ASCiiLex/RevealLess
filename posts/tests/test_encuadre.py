import io
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient

from narrative.services import actualizar_progreso
from ..models import Post
from .utils import crear_obra


def _imagen(nombre):
    buffer = io.BytesIO()
    Image.new('RGB', (2, 2), 'red').save(buffer, 'PNG')
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/png')


class EncuadreGaleriaTests(TestCase):
    def setUp(self):
        media = tempfile.TemporaryDirectory()
        self.addCleanup(media.cleanup)
        ajuste = override_settings(MEDIA_ROOT=media.name)
        ajuste.enable()
        self.addCleanup(ajuste.disable)

        self.client = APIClient()
        self.autor = User.objects.create_user('autor_encuadre', password='x')
        self.obra, self.ep = crear_obra('serie-encuadre', 1)
        actualizar_progreso(self.autor, self.obra, self.ep[0])
        self.client.force_authenticate(user=self.autor)

    def _publicar(self, **extra):
        return self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {
                'text': 'encuadre',
                'referencia_narrativa': self.ep[0].id,
                'frontera_spoiler': self.ep[0].id,
                'imagenes': [_imagen('a.png'), _imagen('b.png')],
                **extra,
            },
            format='multipart',
        )

    def test_guarda_el_encuadre_de_cada_imagen(self):
        response = self._publicar(enfoques_x=[10, 90], enfoques_y=[20, 80], zooms=[150, 100])
        self.assertEqual(response.status_code, 201)
        post = Post.objects.get(id=response.data['id'])
        self.assertEqual(
            list(post.imagenes.values_list('enfoque_x', 'enfoque_y', 'zoom')),
            [(10, 20, 150), (90, 80, 100)],
        )
        self.assertEqual(response.data['imagenes'][0]['zoom'], 150)

    def test_sin_encuadre_usa_centro_y_zoom_base(self):
        post = Post.objects.get(id=self._publicar().data['id'])
        self.assertEqual(list(post.imagenes.values_list('enfoque_x', 'enfoque_y', 'zoom')), [(50, 50, 100)] * 2)

    def test_rechaza_zoom_fuera_de_rango(self):
        self.assertEqual(self._publicar(zooms=[50, 100]).status_code, 400)
        self.assertFalse(Post.objects.exists())