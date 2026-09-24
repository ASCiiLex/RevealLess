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

    def test_crea_post_con_emocion_autor(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {
                'text': 'con emocion', 'referencia_narrativa': self.e1.id,
                'emocion_autor': 'me_encanta',
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['emocion_autor'], 'me_encanta')

    def test_post_sin_emocion_autor_queda_null(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {'text': 'sin emocion', 'referencia_narrativa': self.e1.id},
        )
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data['emocion_autor'])

    def test_rechaza_emocion_autor_invalida(self):
        actualizar_progreso(self.usuario, self.obra, self.e1)
        self.client.force_authenticate(user=self.usuario)

        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {
                'text': 'emocion invalida', 'referencia_narrativa': self.e1.id,
                'emocion_autor': 'no_existe',
            },
        )
        self.assertEqual(response.status_code, 400)


class ReferenciaCruzadaEnPostCreateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('publicador_cruzado', password='x')

        self.anime = Obra.objects.create(titulo='Anime X', slug='anime-x', tipo=Obra.TIPO_SERIE)
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.anime, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.anime.recalcular_orden()
        self.e1.refresh_from_db()

        self.manga = Obra.objects.create(
            titulo='Manga X', slug='manga-x', tipo=Obra.TIPO_MANGA, adapta_a=self.anime,
        )
        self.cap = UnidadNarrativa.objects.create(
            obra=self.manga, tipo='capitulo', nombre='Cap 900', orden_local=1,
        )
        self.manga.recalcular_orden()
        self.cap.refresh_from_db()

        actualizar_progreso(self.usuario, self.anime, self.e1)
        self.client.force_authenticate(user=self.usuario)

    def test_deteccion_bloquea_y_devuelve_detecciones(self):
        response = self.client.post(
            reverse('posts_api_create', args=[self.anime.slug]),
            {'text': 'esto pasó en el manga', 'referencia_narrativa': self.e1.id},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['detail'], 'referencia_cruzada_detectada')
        self.assertEqual(response.data['detecciones'][0]['obra_slug'], self.manga.slug)
        self.assertFalse(Post.objects.filter(text='esto pasó en el manga').exists())

    def test_confirmar_referencia_cruzada_publica_con_ambos_campos(self):
        response = self.client.post(
            reverse('posts_api_create', args=[self.anime.slug]),
            {
                'text': 'esto pasó en el manga', 'referencia_narrativa': self.e1.id,
                'obra_cruzada': self.manga.id, 'frontera_cruzada': self.cap.id,
            },
        )
        self.assertEqual(response.status_code, 201)
        post = Post.objects.get(text='esto pasó en el manga')
        self.assertEqual(post.obra_cruzada, self.manga)
        self.assertEqual(post.frontera_cruzada, self.cap)

    def test_descartar_referencia_cruzada_publica_sin_marcar(self):
        response = self.client.post(
            reverse('posts_api_create', args=[self.anime.slug]),
            {
                'text': 'esto pasó en el manga', 'referencia_narrativa': self.e1.id,
                'descartar_referencia_cruzada': 'true',
            },
        )
        self.assertEqual(response.status_code, 201)
        post = Post.objects.get(text='esto pasó en el manga')
        self.assertIsNone(post.obra_cruzada)

    def test_texto_sin_palabra_clave_no_activa_deteccion(self):
        response = self.client.post(
            reverse('posts_api_create', args=[self.anime.slug]),
            {'text': 'un texto normal sin nada especial', 'referencia_narrativa': self.e1.id},
        )
        self.assertEqual(response.status_code, 201)