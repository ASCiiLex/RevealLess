from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from .models import Post


class PostCreateAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('publicador', password='x')

        self.obra = Obra.objects.create(titulo='Serie Publicar', slug='serie-publicar')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.e3 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E3', orden_local=3,
        )
        self.obra.recalcular_orden()
        for u in (self.e1, self.e2, self.e3):
            u.refresh_from_db()

    def test_requiere_autenticacion(self):
        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {'text': 'hola', 'referencia_narrativa': self.e1.id},
        )
        self.assertEqual(response.status_code, 403)

    def test_sin_progreso_previo_devuelve_409(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {'text': 'hola', 'referencia_narrativa': self.e1.id},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['detail'], 'progreso_requerido')

    def test_crea_post_con_frontera_explicita(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {
                'text': 'con frontera explicita', 'referencia_narrativa': self.e1.id,
                'frontera_spoiler': self.e2.id,
            },
        )
        self.assertEqual(response.status_code, 201)

        post = Post.objects.get(text='con frontera explicita')
        self.assertEqual(post.frontera_origen, ClasificacionNarrativa.ORIGEN_EXPLICITO)
        self.assertEqual(post.frontera_spoiler, self.e2)

    def test_sin_frontera_explicita_cae_a_fallback_sin_api_key(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {'text': 'sin frontera, va a fallback', 'referencia_narrativa': self.e1.id},
        )
        self.assertEqual(response.status_code, 201)

        post = Post.objects.get(text='sin frontera, va a fallback')
        self.assertEqual(post.frontera_origen, ClasificacionNarrativa.ORIGEN_FALLBACK)
        self.assertEqual(post.frontera_spoiler, self.e1)

    def test_actualiza_progreso_desde_el_formulario(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {
                'text': 'avanzando progreso', 'referencia_narrativa': self.e1.id,
                'frontera_spoiler': self.e2.id, 'nuevo_progreso': self.e2.id,
            },
        )

        from narrative.models import ProgresoUsuario
        progreso = ProgresoUsuario.objects.get(usuario=self.usuario, obra=self.obra)
        self.assertEqual(progreso.unidad_actual, self.e2)

    def test_salto_grande_de_progreso_devuelve_409(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        unidades_extra = []
        for i in range(4, 8):
            u = UnidadNarrativa.objects.create(
                obra=self.obra, tipo='episodio', nombre=f'E{i}', orden_local=i,
            )
            unidades_extra.append(u)
        self.obra.recalcular_orden()
        for u in unidades_extra:
            u.refresh_from_db()

        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {
                'text': 'salto grande', 'referencia_narrativa': self.e1.id,
                'frontera_spoiler': unidades_extra[-1].id, 'nuevo_progreso': unidades_extra[-1].id,
            },
        )
        self.assertEqual(response.status_code, 409)
        self.assertTrue(response.data['requiere_confirmacion_progreso'])

    def test_salto_grande_confirmado_se_aplica(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        unidades_extra = []
        for i in range(4, 8):
            u = UnidadNarrativa.objects.create(
                obra=self.obra, tipo='episodio', nombre=f'E{i}', orden_local=i,
            )
            unidades_extra.append(u)
        self.obra.recalcular_orden()
        for u in unidades_extra:
            u.refresh_from_db()

        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {
                'text': 'salto grande confirmado', 'referencia_narrativa': self.e1.id,
                'frontera_spoiler': unidades_extra[-1].id, 'nuevo_progreso': unidades_extra[-1].id,
                'confirmar_salto_progreso': 'true',
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_rechaza_texto_vacio(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {'text': '', 'referencia_narrativa': self.e1.id},
        )
        self.assertEqual(response.status_code, 400)