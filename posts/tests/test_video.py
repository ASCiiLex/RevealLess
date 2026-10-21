import io
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from PIL import Image
from rest_framework.test import APIClient

from narrative.ai_assistant import SugerenciaIA
from narrative.services import actualizar_progreso
from ..models import Post
from ..videos import VideoNoValido, extraer_id_youtube, texto_con_video
from .utils import crear_obra

ID = 'dQw4w9WgXcQ'
VIDEO = {'titulo': 'Tráiler oficial', 'canal': 'Canal oficial'}


def _png():
    buffer = io.BytesIO()
    Image.new('RGB', (2, 2), 'red').save(buffer, 'PNG')
    return SimpleUploadedFile('foto.png', buffer.getvalue(), content_type='image/png')


class ExtraerIdTests(SimpleTestCase):
    def test_formatos_admitidos(self):
        for url in (
            f'https://www.youtube.com/watch?v={ID}&t=10',
            f'https://youtu.be/{ID}',
            f'https://m.youtube.com/watch?v={ID}',
            f'https://www.youtube.com/shorts/{ID}',
            f'https://www.youtube-nocookie.com/embed/{ID}',
        ):
            with self.subTest(url=url):
                self.assertEqual(extraer_id_youtube(url), ID)

    def test_rechaza_lo_que_no_es_youtube(self):
        for url in (
            f'https://vimeo.com/{ID}',
            f'https://youtube.com.malicioso.com/watch?v={ID}',
            'javascript:alert(1)',
            'https://www.youtube.com/watch?v=corto',
            '',
        ):
            with self.subTest(url=url), self.assertRaises(VideoNoValido):
                extraer_id_youtube(url)

    def test_texto_para_la_ia_incluye_el_titulo(self):
        self.assertIn('Tráiler oficial', texto_con_video('Mirad', 'Tráiler oficial', 'Canal'))
        self.assertEqual(texto_con_video('Mirad'), 'Mirad')


@patch('posts.videos.descargar_portada', return_value=None)
@patch('posts.videos.consultar_oembed', return_value=VIDEO)
class PublicarConVideoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('autor_video', password='x')
        self.obra, self.eps = crear_obra('con-video', 3)
        actualizar_progreso(self.usuario, self.obra, self.eps[-1], confirmado=True)
        self.cliente = APIClient()
        self.cliente.force_authenticate(user=self.usuario)

    def _publicar(self, **extra):
        datos = {
            'text': 'Mirad esto',
            'referencia_narrativa': self.eps[0].id,
            'descartar_referencia_cruzada': 'true',
            'video_url': f'https://youtu.be/{ID}',
            **extra,
        }
        return self.cliente.post(f'/posts/api/crear/{self.obra.slug}/', datos, format='multipart')

    def test_guarda_el_video_y_la_api_lo_devuelve(self, *_):
        respuesta = self._publicar(frontera_spoiler=self.eps[0].id)
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(Post.objects.get().video_youtube_id, ID)
        self.assertEqual(respuesta.data['video']['titulo'], 'Tráiler oficial')

    def test_video_e_imagen_a_la_vez_es_400(self, *_):
        respuesta = self._publicar(frontera_spoiler=self.eps[0].id, image=_png())
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(Post.objects.exists())

    def test_enlace_que_no_es_de_youtube_es_400(self, *_):
        respuesta = self._publicar(frontera_spoiler=self.eps[0].id, video_url='https://vimeo.com/1')
        self.assertEqual(respuesta.status_code, 400)

    def test_la_ia_recibe_el_titulo_del_video(self, *_):
        with patch('posts.api_views.crear.proponer_clasificacion', return_value=SugerenciaIA()) as ia:
            self.assertEqual(self._publicar().status_code, 201)
        self.assertIn('Tráiler oficial', ia.call_args.args[0])