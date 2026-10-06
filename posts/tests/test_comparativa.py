import io
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient

from narrative.models import Obra, Personaje
from narrative.services import actualizar_progreso
from subscriptions.services import crear_suscripcion
from ..models import Post
from .utils import crear_obra


def _imagen(nombre='foto.png'):
    buffer = io.BytesIO()
    Image.new('RGB', (2, 2), 'red').save(buffer, 'PNG')
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/png')


def _personaje(nombre, unidad):
    personaje = Personaje.objects.create(nombre=nombre)
    personaje.unidades.add(unidad)
    return personaje


class BasePublicar(TestCase):
    def setUp(self):
        # Las imágenes de prueba no tocan la carpeta media real.
        media = tempfile.TemporaryDirectory()
        self.addCleanup(media.cleanup)
        ajuste = override_settings(MEDIA_ROOT=media.name)
        ajuste.enable()
        self.addCleanup(ajuste.disable)

        self.client = APIClient()
        self.autor = User.objects.create_user('autor_comparativa', password='x')
        self.obra, self.ep = crear_obra('anime-comparativa', 4)
        actualizar_progreso(self.autor, self.obra, self.ep[0])
        self.client.force_authenticate(user=self.autor)

    def _publicar(self, **extra):
        datos = {
            'text': 'comparativa',
            'referencia_narrativa': self.ep[0].id,
            'frontera_spoiler': self.ep[0].id,
            **extra,
        }
        return self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]), datos, format='multipart',
        )


class GaleriaTests(BasePublicar):
    def test_guarda_galeria_con_etiquetas_y_disposicion(self):
        response = self._publicar(
            imagenes=[_imagen('a.png'), _imagen('b.png')], etiquetas=['Anime', 'Manga'], disposicion='deslizador',
        )
        self.assertEqual(response.status_code, 201)
        post = Post.objects.get(id=response.data['id'])
        self.assertEqual(list(post.imagenes.values_list('etiqueta', flat=True)), ['Anime', 'Manga'])
        self.assertEqual(post.disposicion, 'deslizador')
        self.assertEqual([i['etiqueta'] for i in response.data['imagenes']], ['Anime', 'Manga'])

    def test_una_sola_imagen_en_la_lista_se_guarda_como_imagen_simple(self):
        response = self._publicar(imagenes=[_imagen()], disposicion='lado')
        post = Post.objects.get(id=response.data['id'])
        self.assertTrue(post.image)
        self.assertFalse(post.imagenes.exists())
        self.assertEqual(post.disposicion, '')

    def test_rechaza_disposicion_no_valida_para_el_numero(self):
        response = self._publicar(imagenes=[_imagen('a.png'), _imagen('b.png')], disposicion='cuadricula')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Post.objects.exists())

    def test_rechaza_mas_de_cuatro_imagenes(self):
        response = self._publicar(imagenes=[_imagen(f'{i}.png') for i in range(5)])
        self.assertEqual(response.status_code, 400)

    def test_rechaza_imagen_y_galeria_a_la_vez(self):
        response = self._publicar(image=_imagen(), imagenes=[_imagen('a.png'), _imagen('b.png')])
        self.assertEqual(response.status_code, 400)


class PersonajesComparadosTests(BasePublicar):
    def setUp(self):
        super().setUp()
        self.luffy = _personaje('Luffy', self.ep[0])
        self.kaido = _personaje('Kaido', self.ep[3])

    def test_guarda_personajes_en_el_orden_elegido(self):
        response = self._publicar(personajes_comparados=[self.kaido.id, self.luffy.id])
        self.assertEqual(response.status_code, 201)
        self.assertEqual([p['nombre'] for p in response.data['personajes_comparados']], ['Kaido', 'Luffy'])
        post = Post.objects.get(id=response.data['id'])
        self.assertEqual(set(post.personajes.all()), {self.luffy, self.kaido})

    def test_eleva_la_frontera_hasta_el_personaje_mas_tardio(self):
        response = self._publicar(personajes_comparados=[self.luffy.id, self.kaido.id])
        post = Post.objects.get(id=response.data['id'])
        self.assertEqual(post.frontera_spoiler, self.ep[3])

    def test_rechaza_un_solo_personaje(self):
        self.assertEqual(self._publicar(personajes_comparados=[self.luffy.id]).status_code, 400)

    def test_rechaza_personaje_de_otra_obra_no_comparada(self):
        _, (otra_unidad,) = crear_obra('otra-obra-comparativa')
        goku = _personaje('Goku', otra_unidad)
        response = self._publicar(personajes_comparados=[self.luffy.id, goku.id])
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Post.objects.exists())


class CruceDeObrasTests(BasePublicar):
    def setUp(self):
        super().setUp()
        self.manga, self.caps = crear_obra('manga-comparativa', 2, tipo_unidad='capitulo', tipo=Obra.TIPO_MANGA)
        self.luffy = _personaje('Luffy', self.ep[0])
        self.shanks = _personaje('Shanks', self.caps[1])

    def _publicar_cruce(self):
        return self._publicar(
            obra_cruzada=self.manga.id, frontera_cruzada=self.caps[0].id,
            personajes_comparados=[self.luffy.id, self.shanks.id],
        )

    def test_personaje_de_la_obra_cruzada_eleva_su_frontera(self):
        response = self._publicar_cruce()
        self.assertEqual(response.status_code, 201)
        post = Post.objects.get(id=response.data['id'])
        self.assertEqual(post.frontera_cruzada, self.caps[1])
        self.assertEqual(response.data['obra_cruzada']['slug'], self.manga.slug)

    def _ids_feed(self, usuario, **params):
        cliente = APIClient()
        cliente.force_authenticate(user=usuario)
        return [p['id'] for p in cliente.get(reverse('narrative_api_feed'), params).data['results']]

    def test_llega_a_quien_sigue_solo_la_obra_cruzada_con_ambas_fronteras(self):
        post_id = self._publicar_cruce().data['id']
        lectora = User.objects.create_user('lectora_manga', password='x')
        crear_suscripcion(lectora, self.manga)
        actualizar_progreso(lectora, self.obra, self.ep[0])
        actualizar_progreso(lectora, self.manga, self.caps[1])

        self.assertIn(post_id, self._ids_feed(lectora))
        self.assertIn(post_id, self._ids_feed(lectora, obra=self.manga.id))

    def test_sin_progreso_en_la_obra_cruzada_no_lo_ve(self):
        post_id = self._publicar_cruce().data['id']
        lector = User.objects.create_user('lector_solo_anime', password='x')
        crear_suscripcion(lector, self.manga)
        actualizar_progreso(lector, self.obra, self.ep[0])

        self.assertNotIn(post_id, self._ids_feed(lector))