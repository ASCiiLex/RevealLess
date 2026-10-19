from django.contrib.auth.models import User
from django.test import TestCase

from comments.models import Comment
from narrative.models import ClasificacionNarrativa, Obra, UnidadNarrativa
from narrative.services import actualizar_progreso, asegurar_unidad_previa
from posts.models import Post
from posts.tests.utils import crear_obra, crear_post

EXPLICITO = ClasificacionNarrativa.ORIGEN_EXPLICITO


def _unidad(obra, nombre, orden_local, padre=None, tipo='episodio', **campos):
    return UnidadNarrativa.objects.create(
        obra=obra, padre=padre, tipo=tipo, nombre=nombre, orden_local=orden_local, **campos,
    )


class PreviaObraNuevaTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('autor_previa', password='x')
        self.lector = User.objects.create_user('lector_previa', password='x')
        self.obra = Obra.objects.create(titulo='Por estrenar', slug='previa-nueva')
        self.previa = asegurar_unidad_previa(self.obra)
        self.post = crear_post(self.autor, self.obra, self.previa)

    def test_la_frontera_previa_de_una_obra_nueva_es_cero(self):
        self.assertEqual(self.post.frontera_orden, 0)

    def test_visible_sin_progreso_declarado(self):
        self.assertIn(self.post, Post.objects.visible_for(self.lector))

    def test_comentario_heredado_visible_sin_progreso(self):
        comentario = Comment.objects.create(
            user=self.autor, post=self.post, text='c', referencia_narrativa=self.previa,
        )
        self.assertIn(comentario, Comment.objects.visible_for(self.lector))

    def test_comentario_con_frontera_previa_propia_visible_sin_progreso(self):
        comentario = Comment.objects.create(
            user=self.autor, post=self.post, text='c', referencia_narrativa=self.previa,
            frontera_spoiler=self.previa, frontera_origen=EXPLICITO,
        )
        self.assertEqual(comentario.frontera_orden, 0)
        self.assertIn(comentario, Comment.objects.visible_for(self.lector))

    def test_tras_cargar_episodios_la_previa_sigue_visible_y_el_resto_oculto(self):
        piloto = _unidad(self.obra, 'Piloto', 1)
        self.obra.recalcular_orden()
        piloto.refresh_from_db()
        post_piloto = crear_post(self.autor, self.obra, piloto)
        self.post.refresh_from_db()

        visibles = Post.objects.visible_for(self.lector)
        self.assertEqual(self.post.frontera_orden, 0)
        self.assertIn(self.post, visibles)
        self.assertNotIn(post_piloto, visibles)


class PreviaContinuacionTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('autor_cont', password='x')
        self.al_dia = User.objects.create_user('al_dia_cont', password='x')
        self.atrasado = User.objects.create_user('atrasado_cont', password='x')

        self.obra = Obra.objects.create(titulo='Serie larga', slug='previa-continuacion')
        t1 = _unidad(self.obra, 'Temporada 1', 1, tipo='temporada')
        self.e1 = _unidad(self.obra, 'E1', 1, padre=t1)
        self.e2 = _unidad(self.obra, 'E2', 2, padre=t1)
        t2 = _unidad(self.obra, 'Temporada 2', 2, tipo='temporada')
        self.previa_t2 = _unidad(
            self.obra, 'Previo al estreno', 0, padre=t2, tipo=UnidadNarrativa.TIPO_PREVIO,
        )
        self.e3 = _unidad(self.obra, 'E3', 1, padre=t2)
        self.obra.recalcular_orden()
        for unidad in (self.e1, self.e2, self.previa_t2, self.e3):
            unidad.refresh_from_db()

        actualizar_progreso(self.al_dia, self.obra, self.e2)
        actualizar_progreso(self.atrasado, self.obra, self.e1)
        self.post = crear_post(self.autor, self.obra, self.previa_t2)

    def test_exige_el_final_de_la_entrega_anterior(self):
        self.assertEqual(self.post.frontera_orden, self.e2.orden_fin)

    def test_visible_para_quien_esta_al_dia(self):
        self.assertIn(self.post, Post.objects.visible_for(self.al_dia))

    def test_oculto_para_quien_va_atrasado(self):
        self.assertNotIn(self.post, Post.objects.visible_for(self.atrasado))

    def test_declarar_la_previa_no_desbloquea_la_entrega(self):
        actualizar_progreso(self.al_dia, self.obra, self.previa_t2)
        post_e3 = crear_post(self.autor, self.obra, self.e3)

        visibles = Post.objects.visible_for(self.al_dia)
        self.assertIn(self.post, visibles)
        self.assertNotIn(post_e3, visibles)


class PreviaCruzadaTests(TestCase):
    def test_frontera_cruzada_en_previa_de_obra_nueva_no_exige_progreso(self):
        autor = User.objects.create_user('autor_cruce_previa', password='x')
        lector = User.objects.create_user('lector_cruce_previa', password='x')
        obra, (e1,) = crear_obra('previa-cruce-origen')
        estreno = Obra.objects.create(titulo='Secuela', slug='previa-cruce-secuela')
        previa = asegurar_unidad_previa(estreno)
        actualizar_progreso(lector, obra, e1)

        post = Post.objects.create(
            author=autor, obra=obra, text='cruce',
            referencia_narrativa=e1, frontera_spoiler=e1, frontera_origen=EXPLICITO,
            obra_cruzada=estreno, frontera_cruzada=previa,
        )
        self.assertEqual(post.frontera_cruzada_orden, 0)
        self.assertIn(post, Post.objects.visible_for(lector))


class RefrescoFronterasTests(TestCase):
    def test_recalcular_orden_actualiza_las_fronteras_cacheadas(self):
        autor = User.objects.create_user('autor_refresco', password='x')
        obra, (e1, e2) = crear_obra('refresco-fronteras', n=2)
        otra, (x1,) = crear_obra('refresco-otra')

        post = crear_post(autor, obra, e1, frontera=e2)
        comentario = Comment.objects.create(
            user=autor, post=post, text='c', referencia_narrativa=e1,
            frontera_spoiler=e2, frontera_origen=EXPLICITO,
        )
        cruzado = Post.objects.create(
            author=autor, obra=otra, text='cruce',
            referencia_narrativa=x1, frontera_spoiler=x1, frontera_origen=EXPLICITO,
            obra_cruzada=obra, frontera_cruzada=e2,
        )
        self.assertEqual(post.frontera_orden, 2)

        # Insertado al principio: desplaza e2 de la posición 2 a la 3.
        _unidad(obra, 'Insertado', 3, orden_manual=1)
        obra.recalcular_orden()

        for objeto in (post, comentario, cruzado):
            objeto.refresh_from_db()
        self.assertEqual(post.frontera_orden, 3)
        self.assertEqual(comentario.frontera_orden, 3)
        self.assertEqual(cruzado.frontera_cruzada_orden, 3)
        self.assertEqual(cruzado.frontera_orden, 1)