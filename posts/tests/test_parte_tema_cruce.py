from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, TemaTransversal
from narrative.services import actualizar_progreso
from ..models import Post
from .utils import crear_obra


class ParteOTemaTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('autor_tema', password='x')
        self.obra, self.ep = crear_obra('serie-parte-tema', 2)
        actualizar_progreso(self.autor, self.obra, self.ep[0])
        self.tema = TemaTransversal.objects.create(obra=self.obra, nombre='Haki')
        self.client.force_authenticate(user=self.autor)

    def _publicar(self, con_frontera=True, **extra):
        datos = {'text': 'sobre el haki', **extra}
        if con_frontera:
            datos['frontera_spoiler'] = self.ep[0].id
        return self.client.post(reverse('posts_api_create', args=[self.obra.slug]), datos)

    def test_solo_tema_sin_parte(self):
        response = self._publicar(tema=self.tema.id)
        self.assertEqual(response.status_code, 201)
        post = Post.objects.get(id=response.data['id'])
        self.assertIsNone(post.referencia_narrativa)
        self.assertEqual(response.data['temas'], [{'id': self.tema.id, 'nombre': 'Haki'}])

    def test_solo_tema_propuesto(self):
        self.assertEqual(self._publicar(tema_propuesto='Frutas del diablo').status_code, 201)

    def test_solo_frontera_la_usa_como_parte(self):
        response = self._publicar()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Post.objects.get(id=response.data['id']).referencia_narrativa, self.ep[0])

    def test_sin_parte_tema_ni_frontera_devuelve_400(self):
        self.assertEqual(self._publicar(con_frontera=False).status_code, 400)
        self.assertFalse(Post.objects.exists())

    def test_con_parte_sigue_funcionando(self):
        self.assertEqual(self._publicar(referencia_narrativa=self.ep[0].id).status_code, 201)


class ModoCruceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('autor_cruce', password='x')
        self.manga, self.caps = crear_obra('manga-escena', 2, tipo_unidad='capitulo', tipo=Obra.TIPO_MANGA)
        self.anime, self.eps = crear_obra('anime-escena', 2, adapta_a=self.manga)
        self.otra, _ = crear_obra('otra-escena')
        actualizar_progreso(self.autor, self.anime, self.eps[1])
        self.client.force_authenticate(user=self.autor)

    def _publicar(self, obra_cruzada, frontera_cruzada, modo):
        return self.client.post(
            reverse('posts_api_create', args=[self.anime.slug]),
            {
                'text': 'la misma escena',
                'referencia_narrativa': self.eps[1].id,
                'frontera_spoiler': self.eps[1].id,
                'obra_cruzada': obra_cruzada.id,
                'frontera_cruzada': frontera_cruzada.id,
                'modo_cruce': modo,
            },
        )

    def _lector(self, nombre, progresos):
        lector = User.objects.create_user(nombre, password='x')
        for obra, unidad in progresos:
            actualizar_progreso(lector, obra, unidad)
        return lector

    def test_misma_escena_basta_con_una_frontera(self):
        post = Post.objects.get(id=self._publicar(self.manga, self.caps[1], Post.MODO_MISMA_ESCENA).data['id'])
        solo_manga = self._lector('solo_manga', [(self.manga, self.caps[1])])
        solo_anime = self._lector('solo_anime', [(self.anime, self.eps[1])])
        sin_llegar = self._lector('sin_llegar', [(self.anime, self.eps[0]), (self.manga, self.caps[0])])

        self.assertIn(post, Post.objects.visible_for(solo_manga))
        self.assertIn(post, Post.objects.visible_for(solo_anime))
        self.assertNotIn(post, Post.objects.visible_for(sin_llegar))

    def test_comparativa_exige_ambas_fronteras(self):
        post = Post.objects.get(id=self._publicar(self.manga, self.caps[1], Post.MODO_COMPARATIVA).data['id'])
        solo_manga = self._lector('solo_manga_c', [(self.manga, self.caps[1])])
        ambas = self._lector('ambas', [(self.anime, self.eps[1]), (self.manga, self.caps[1])])

        self.assertNotIn(post, Post.objects.visible_for(solo_manga))
        self.assertIn(post, Post.objects.visible_for(ambas))

    def test_misma_escena_entre_obras_no_relacionadas_devuelve_400(self):
        unidad_otra = self.otra.unidades.get()
        response = self._publicar(self.otra, unidad_otra, Post.MODO_MISMA_ESCENA)
        self.assertEqual(response.status_code, 400)