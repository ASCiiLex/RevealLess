from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import EtapaPersonaje, Personaje
from narrative.serializers import PostSerializer
from narrative.services import actualizar_progreso
from posts.models import PersonajeComparado, Post
from posts.tests.utils import crear_obra, crear_post
from subscriptions.services import crear_suscripcion, filtro_posts_suscripciones


def _personaje(nombre, unidad, identidad_de=None):
    personaje = Personaje.objects.create(nombre=nombre, identidad_de=identidad_de)
    personaje.unidades.add(unidad)
    return personaje


class IdentidadesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.lector = User.objects.create_user('lector_identidades', password='x')
        self.autor = User.objects.create_user('autor_identidades', password='x')
        self.obra, self.ep = crear_obra('serie-identidades', 6)
        crear_suscripcion(self.lector, obra=self.obra)

        self.usopp = _personaje('Usopp', self.ep[0])
        self.sogeking = _personaje('Sogeking', self.ep[1], identidad_de=self.usopp)
        self.obito = _personaje('Obito', self.ep[2])
        self.tobi = _personaje('Tobi', self.ep[3], identidad_de=self.obito)
        self.tobi.identidad_revelada_tras.add(self.ep[5])

        self.post_usopp = self._post_de(self.usopp, self.ep[0])
        self.post_sogeking = self._post_de(self.sogeking, self.ep[1])
        self.post_obito = self._post_de(self.obito, self.ep[2])
        self.post_tobi = self._post_de(self.tobi, self.ep[3])
        self.client.force_authenticate(user=self.lector)

    def _post_de(self, personaje, unidad):
        post = crear_post(self.autor, self.obra, unidad)
        post.personajes.add(personaje)
        return post

    def _avanzar(self, unidad):
        actualizar_progreso(self.lector, self.obra, unidad, confirmado=True)

    def _feed(self, personaje):
        response = self.client.get(reverse('narrative_api_feed'), {'personaje': personaje.id})
        return {p['id'] for p in response.data['results']}

    def _landing(self, personaje):
        return self.client.get(reverse('narrative_api_personaje_landing', args=[personaje.id])).json()

    def test_feed_de_usopp_incluye_a_sogeking(self):
        self._avanzar(self.ep[1])
        self.assertEqual(self._feed(self.usopp), {self.post_usopp.id, self.post_sogeking.id})

    def test_feed_de_sogeking_solo_lo_suyo(self):
        self._avanzar(self.ep[1])
        self.assertEqual(self._feed(self.sogeking), {self.post_sogeking.id})

    def test_landings_vinculadas_desde_la_primera_aparicion(self):
        self._avanzar(self.ep[1])
        self.assertEqual(self._landing(self.sogeking)['identidad_de'], {'id': self.usopp.id, 'nombre': 'Usopp'})
        self.assertEqual(
            self._landing(self.usopp)['otras_identidades'], [{'id': self.sogeking.id, 'nombre': 'Sogeking'}],
        )

    def test_tobi_y_obito_separados_antes_de_la_revelacion(self):
        self._avanzar(self.ep[4])
        self.assertEqual(self._feed(self.obito), {self.post_obito.id})
        self.assertEqual(self._landing(self.obito)['otras_identidades'], [])
        self.assertIsNone(self._landing(self.tobi)['identidad_de'])

    def test_tobi_y_obito_vinculados_tras_la_revelacion(self):
        self._avanzar(self.ep[5])
        self.assertEqual(self._feed(self.obito), {self.post_obito.id, self.post_tobi.id})
        self.assertEqual(self._landing(self.tobi)['identidad_de']['nombre'], 'Obito')
        self.assertEqual(self._feed(self.tobi), {self.post_tobi.id})

    def test_la_suscripcion_a_usopp_incluye_a_sogeking(self):
        fan = User.objects.create_user('fan_usopp', password='x')
        actualizar_progreso(fan, self.obra, self.ep[1])
        crear_suscripcion(fan, personaje=self.usopp)
        ids = set(Post.objects.filter(filtro_posts_suscripciones(fan)).values_list('id', flat=True))
        self.assertEqual(ids, {self.post_usopp.id, self.post_sogeking.id})

    def test_no_se_encadenan_identidades(self):
        disfraz = Personaje(nombre='Disfraz de Sogeking', identidad_de=self.sogeking)
        with self.assertRaises(ValidationError):
            disfraz.full_clean()


class NombresSegunProgresoTests(TestCase):
    """Datos como Robin en One Piece: nombre base «Nico Robin», alias «Miss All Sunday»
    desde su aparición y de vuelta a «Nico Robin» tras la revelación."""

    def setUp(self):
        self.client = APIClient()
        self.lector = User.objects.create_user('lector_nombres', password='x')
        self.obra, self.ep = crear_obra('serie-nombres', 3)
        self.robin = _personaje('Nico Robin', self.ep[0])
        EtapaPersonaje.objects.create(personaje=self.robin, visible_tras=self.ep[0], alias='Miss All Sunday')
        EtapaPersonaje.objects.create(personaje=self.robin, visible_tras=self.ep[2], alias='Nico Robin')
        self.crocodile = _personaje('Crocodile', self.ep[0])
        self.client.force_authenticate(user=self.lector)

    def _buscar(self, q=''):
        url = reverse('narrative_api_personajes_publicar', args=[self.obra.slug])
        return [p['nombre'] for p in self.client.get(url, {'q': q}).data['personajes']]

    def test_antes_de_la_revelacion_no_se_encuentra_por_el_nombre_oculto(self):
        actualizar_progreso(self.lector, self.obra, self.ep[1])
        self.assertEqual(self._buscar('nico'), [])
        self.assertEqual(self._buscar('miss'), ['Miss All Sunday'])
        self.assertNotIn('Nico Robin', self._buscar())

    def test_tras_la_revelacion_se_muestra_el_nombre_real(self):
        actualizar_progreso(self.lector, self.obra, self.ep[2])
        self.assertEqual(self._buscar('nico'), ['Nico Robin'])
        self.assertEqual(self._buscar('miss'), ['Nico Robin'])

    def test_la_cabecera_vs_usa_el_nombre_de_la_frontera_del_post(self):
        autor = User.objects.create_user('autor_nombres', password='x')
        post = crear_post(autor, self.obra, self.ep[1])
        PersonajeComparado.objects.bulk_create([
            PersonajeComparado(post=post, personaje=self.robin, orden=0),
            PersonajeComparado(post=post, personaje=self.crocodile, orden=1),
        ])
        nombres = [p['nombre'] for p in PostSerializer(post).data['personajes_comparados']]
        self.assertEqual(nombres, ['Miss All Sunday', 'Crocodile'])