from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Personaje, PropuestaAparicion, SolicitudPersonaje
from narrative.services import actualizar_progreso
from narrative.services.personajes import aprobar_solicitud_personaje, rechazar_solicitud_personaje
from posts.models import Post
from posts.tests.utils import crear_obra


class SolicitudPersonajeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('proponente', password='x')
        self.obra, self.ep = crear_obra('serie-solicitud-personaje', 3)
        actualizar_progreso(self.autor, self.obra, self.ep[1])
        self.luffy = Personaje.objects.create(nombre='Luffy')
        self.luffy.unidades.add(self.ep[0])
        self.client.force_authenticate(user=self.autor)

    def _publicar(self, propuestos=('Katakuri',), texto='Luffy vs Katakuri'):
        return self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {
                'text': texto,
                'referencia_narrativa': self.ep[1].id,
                'frontera_spoiler': self.ep[1].id,
                'personajes_comparados': [self.luffy.id],
                'personajes_propuestos': list(propuestos),
            },
            format='multipart',
        )

    def test_propuesta_crea_solicitud_y_comparado_pendiente(self):
        response = self._publicar()
        self.assertEqual(response.status_code, 201)
        solicitud = SolicitudPersonaje.objects.get()
        self.assertEqual((solicitud.nombre, solicitud.unidad), ('Katakuri', self.ep[1]))
        self.assertEqual(
            [(p['nombre'], p['pendiente']) for p in response.data['personajes_comparados']],
            [('Luffy', False), ('Katakuri', True)],
        )

    def test_la_misma_propuesta_reutiliza_la_solicitud(self):
        self._publicar()
        self._publicar(propuestos=('katakuri',), texto='otra vez')
        self.assertEqual(SolicitudPersonaje.objects.count(), 1)

    def test_aprobar_crea_personaje_aparicion_y_vinculo(self):
        post = Post.objects.get(id=self._publicar().data['id'])
        aprobar_solicitud_personaje(SolicitudPersonaje.objects.get())

        katakuri = Personaje.objects.get(nombre='Katakuri')
        self.assertIn(self.ep[1], katakuri.unidades.all())
        self.assertEqual(
            PropuestaAparicion.objects.get(personaje=katakuri).estado, PropuestaAparicion.ESTADO_APROBADA,
        )
        self.assertEqual([c.personaje for c in post.comparaciones.all()], [self.luffy, katakuri])
        self.assertIn(katakuri, post.personajes.all())

    def test_aprobar_con_personaje_existente_elegido_no_duplica(self):
        self._publicar()
        existente = Personaje.objects.create(nombre='Charlotte Katakuri')
        solicitud = SolicitudPersonaje.objects.get()
        solicitud.personaje = existente
        solicitud.save()

        aprobar_solicitud_personaje(solicitud)
        self.assertFalse(Personaje.objects.filter(nombre='Katakuri').exists())
        self.assertIn(self.ep[1], existente.unidades.all())

    def test_rechazar_lo_retira_del_post(self):
        post = Post.objects.get(id=self._publicar().data['id'])
        rechazar_solicitud_personaje(SolicitudPersonaje.objects.get())
        self.assertEqual([c.personaje for c in post.comparaciones.all()], [self.luffy])