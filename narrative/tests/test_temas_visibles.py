from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import TemaTransversal
from narrative.services import actualizar_progreso
from posts.models import Post
from posts.tests.utils import crear_obra


class TemasVisiblesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('lector_temas', password='x')
        self.obra, self.eps = crear_obra('temas-visibles', 3)
        self.general = TemaTransversal.objects.create(obra=self.obra, nombre='Tema general')
        self.mini = TemaTransversal.objects.create(
            obra=self.obra, nombre='Minihistoria secreta', tipo=TemaTransversal.TIPO_MINIHISTORIA,
        )
        self.mini.unidades.add(self.eps[2])
        actualizar_progreso(self.usuario, self.obra, self.eps[0])
        self.client.force_authenticate(user=self.usuario)

    def _nombres(self, temas):
        return {t['nombre'] for t in temas}

    def test_queryset_oculta_la_minihistoria_hasta_alcanzarla(self):
        self.assertEqual(set(TemaTransversal.objects.visibles_para(self.usuario)), {self.general})
        actualizar_progreso(self.usuario, self.obra, self.eps[2])
        self.assertEqual(set(TemaTransversal.objects.visibles_para(self.usuario)), {self.general, self.mini})

    def test_buscador(self):
        datos = self.client.get(reverse('narrative_api_buscar'), {'q': 'tema'}).data
        self.assertEqual(self._nombres(datos['temas']), {'Tema general'})
        self.assertEqual(self.client.get(reverse('narrative_api_buscar'), {'q': 'secreta'}).data['temas'], [])

    def test_landing_de_obra(self):
        datos = self.client.get(reverse('narrative_api_obra_landing', args=[self.obra.slug])).data
        self.assertEqual(self._nombres(datos['temas']), {'Tema general'})

    def test_landing_de_tema_no_alcanzado_da_404(self):
        self.assertEqual(self.client.get(reverse('narrative_api_tema_landing', args=[self.mini.id])).status_code, 404)
        self.assertEqual(self.client.get(reverse('narrative_api_tema_landing', args=[self.general.id])).status_code, 200)

    def test_selectores_de_publicar(self):
        publicar = self.client.get(reverse('narrative_api_obras_publicar')).data
        contexto = self.client.get(reverse('narrative_api_obra_contexto_publicar', args=[self.obra.slug])).data
        self.assertEqual(self._nombres(publicar['temas']), {'Tema general'})
        self.assertEqual(self._nombres(contexto['temas']), {'Tema general'})


class FronteraPorTemaTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('autor_temas', password='x')
        self.obra, self.eps = crear_obra('frontera-tema', 3)
        self.mini = TemaTransversal.objects.create(
            obra=self.obra, nombre='Minihistoria', tipo=TemaTransversal.TIPO_MINIHISTORIA,
        )
        self.mini.unidades.add(self.eps[2])
        actualizar_progreso(self.autor, self.obra, self.eps[2])
        self.client.force_authenticate(user=self.autor)

    def _publicar(self, **datos):
        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {'text': 'x', 'frontera_spoiler': self.eps[0].id, **datos},
        )
        self.assertEqual(response.status_code, 201)
        return Post.objects.get(id=response.data['id'])

    def test_el_tema_eleva_la_frontera_a_su_primera_unidad(self):
        self.assertEqual(self._publicar(tema=self.mini.id).frontera_spoiler, self.eps[2])

    def test_un_tema_propuesto_que_ya_existe_tambien_la_eleva(self):
        post = self._publicar(tema_propuesto='minihistoria')
        self.assertEqual(post.frontera_spoiler, self.eps[2])
        self.assertEqual(list(post.temas_transversales.all()), [self.mini])