import io
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from saved_posts.models import SavedPost
from ..models import Post, PostImagen
from .utils import crear_obra, crear_post


def _imagen(nombre):
    buffer = io.BytesIO()
    Image.new('RGB', (2, 2), 'red').save(buffer, 'PNG')
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/png')


class ImagenesMiniaturaTests(TestCase):
    def setUp(self):
        # Las imágenes de prueba no tocan la carpeta media real.
        media = tempfile.TemporaryDirectory()
        self.addCleanup(media.cleanup)
        ajuste = override_settings(MEDIA_ROOT=media.name)
        ajuste.enable()
        self.addCleanup(ajuste.disable)

        self.autor = User.objects.create_user('autor_galeria', password='x')
        obra, (unidad,) = crear_obra('imagenes-miniatura')
        self.post = crear_post(self.autor, obra, unidad)
        self.cliente = APIClient()
        self.cliente.force_authenticate(user=self.autor)

    def _galeria(self):
        self.post.disposicion = Post.DISPOSICION_APILADAS
        self.post.save(update_fields=['disposicion'])
        segunda = PostImagen.objects.create(post=self.post, imagen=_imagen('b.png'), orden=1, zoom=150)
        primera = PostImagen.objects.create(post=self.post, imagen=_imagen('a.png'), orden=0, etiqueta='Anime')
        return [primera.image_url, segunda.image_url]

    def test_sin_fotos_lista_vacia(self):
        self.assertEqual(self.post.imagenes_para_mostrar(), [])

    def test_galeria_en_orden_con_su_encuadre(self):
        urls = self._galeria()
        imagenes = self.post.imagenes_para_mostrar()
        self.assertEqual([i['url'] for i in imagenes], urls)
        self.assertEqual((imagenes[0]['etiqueta'], imagenes[1]['zoom']), ('Anime', 150))

    def test_el_perfil_devuelve_la_composicion(self):
        urls = self._galeria()
        post = self.cliente.get(f'/perfil/api/{self.autor.username}/').data['posts'][0]
        self.assertEqual([i['url'] for i in post['imagenes']], urls)
        self.assertEqual(post['disposicion'], Post.DISPOSICION_APILADAS)

    def test_guardados_devuelve_la_composicion(self):
        urls = self._galeria()
        SavedPost.objects.create(user=self.autor, post=self.post)
        guardado = self.cliente.get('/guardados/api/').data[0]
        self.assertEqual([i['url'] for i in guardado['imagenes']], urls)
        self.assertEqual(guardado['disposicion'], Post.DISPOSICION_APILADAS)