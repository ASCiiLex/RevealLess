from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from posts.models import Post
from ..models import Comment

TEXTO = 'esto pasó en el manga'


class DeteccionReferenciaCruzadaComentarioTests(TestCase):
    def setUp(self):
        autor = User.objects.create_user('deteccion_autor', password='x')
        comentador = User.objects.create_user('deteccion_comentador', password='x')

        anime = Obra.objects.create(titulo='Anime Y', slug='anime-y', tipo=Obra.TIPO_SERIE)
        e1 = UnidadNarrativa.objects.create(obra=anime, tipo='episodio', nombre='E1', orden_local=1)
        anime.recalcular_orden()
        e1.refresh_from_db()
        actualizar_progreso(comentador, anime, e1)

        self.manga = Obra.objects.create(
            titulo='Manga Y', slug='manga-y-rel', tipo=Obra.TIPO_MANGA, adapta_a=anime,
        )
        self.cap = UnidadNarrativa.objects.create(
            obra=self.manga, tipo='capitulo', nombre='Cap 900', orden_local=1,
        )
        self.manga.recalcular_orden()
        self.cap.refresh_from_db()

        self.post = Post.objects.create(
            author=autor, obra=anime, text='post base',
            referencia_narrativa=e1, frontera_spoiler=e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.client.force_login(comentador)

    def _comentar(self, **extra):
        return self.client.post(reverse('add_comment'), {'post_id': self.post.id, 'text': TEXTO, **extra})

    def test_deteccion_bloquea_comentario_y_devuelve_detecciones(self):
        response = self._comentar()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['detail'], 'referencia_cruzada_detectada')
        self.assertFalse(Comment.objects.filter(text=TEXTO).exists())

    def test_descartar_referencia_cruzada_permite_comentar(self):
        response = self._comentar(descartar_referencia_cruzada='true')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(Comment.objects.get(text=TEXTO).obra_cruzada)

    def test_obra_cruzada_explicita_evita_la_deteccion(self):
        response = self._comentar(obra_cruzada=self.manga.id, frontera_cruzada=self.cap.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.get(text=TEXTO).obra_cruzada, self.manga)