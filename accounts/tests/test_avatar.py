import io
import shutil
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient


def _imagen(nombre, formato):
    buffer = io.BytesIO()
    Image.new('RGB', (10, 10), 'red').save(buffer, format=formato)
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type=f'image/{formato.lower()}')


class AvatarRegistroTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)

    def _datos(self, imagen):
        return {
            'username': 'avatar_nuevo',
            'email': 'avatar_nuevo@example.com',
            'password': 'Contraseña-Segura-91',
            'password2': 'Contraseña-Segura-91',
            'image': imagen,
        }

    def test_registro_con_avatar_valido(self):
        with override_settings(MEDIA_ROOT=self.media):
            response = self.client.post(
                reverse('accounts_api_register'), self._datos(_imagen('avatar.png', 'PNG')),
                format='multipart',
            )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.get(username='avatar_nuevo').profile.image)

    def test_registro_rechaza_extension_no_permitida(self):
        response = self.client.post(
            reverse('accounts_api_register'), self._datos(_imagen('avatar.gif', 'GIF')),
            format='multipart',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('image', response.data)
        self.assertFalse(User.objects.filter(username='avatar_nuevo').exists())

    def test_registro_rechaza_imagen_demasiado_grande(self):
        with patch('core.validators.MAX_IMAGE_SIZE_MB', 0):
            response = self.client.post(
                reverse('accounts_api_register'), self._datos(_imagen('avatar.png', 'PNG')),
                format='multipart',
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn('image', response.data)
        self.assertFalse(User.objects.filter(username='avatar_nuevo').exists())


class AvatarEdicionPerfilTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('avatar_editor', email='editor@example.com', password='x')
        self.client.force_authenticate(user=self.usuario)

    def _datos(self, imagen):
        return {'username': 'avatar_editor', 'email': 'editor@example.com', 'image': imagen}

    def test_edicion_rechaza_extension_no_permitida(self):
        response = self.client.patch(
            reverse('profiles_api_edit'), self._datos(_imagen('avatar.gif', 'GIF')),
            format='multipart',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('image', response.data)

    def test_edicion_rechaza_imagen_demasiado_grande(self):
        with patch('core.validators.MAX_IMAGE_SIZE_MB', 0):
            response = self.client.patch(
                reverse('profiles_api_edit'), self._datos(_imagen('avatar.png', 'PNG')),
                format='multipart',
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn('image', response.data)