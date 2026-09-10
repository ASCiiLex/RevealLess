from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from posts.models import Post
from .models import Suscripcion, TemaTransversal
from .services import (
    crear_suscripcion,
    eliminar_suscripcion,
    marcar_visto,
    posts_no_leidos_count,
)


class TemaTransversalTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo='One Piece', slug='one-piece')

    def test_unique_together_obra_nombre(self):
        TemaTransversal.objects.create(obra=self.obra, nombre='Frutas del diablo')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TemaTransversal.objects.create(obra=self.obra, nombre='Frutas del diablo')

    def test_mismo_nombre_en_distinta_obra_es_valido(self):
        otra_obra = Obra.objects.create(titulo='Otra', slug='otra')
        TemaTransversal.objects.create(obra=self.obra, nombre='Poder')
        TemaTransversal.objects.create(obra=otra_obra, nombre='Poder')
        self.assertEqual(TemaTransversal.objects.count(), 2)


class SuscripcionModeloTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('lector', password='x')
        self.obra = Obra.objects.create(titulo='Serie', slug='serie')
        self.otra_obra = Obra.objects.create(titulo='Otra', slug='otra')
        self.unidad = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='arco', nombre='Arco', orden_local=1,
        )
        self.unidad_otra_obra = UnidadNarrativa.objects.create(
            obra=self.otra_obra, tipo='episodio', nombre='X1', orden_local=1,
        )
        self.tema = TemaTransversal.objects.create(obra=self.obra, nombre='Frutas del diablo')
        self.tema_otra_obra = TemaTransversal.objects.create(obra=self.otra_obra, nombre='Otro tema')

    def test_suscripcion_a_nivel_obra(self):
        suscripcion = Suscripcion.objects.create(usuario=self.usuario, obra=self.obra)
        self.assertEqual(suscripcion.nivel, 'obra')

    def test_suscripcion_a_nivel_unidad(self):
        suscripcion = Suscripcion.objects.create(
            usuario=self.usuario, obra=self.obra, unidad=self.unidad,
        )
        self.assertEqual(suscripcion.nivel, 'unidad')

    def test_suscripcion_a_nivel_tema(self):
        suscripcion = Suscripcion.objects.create(
            usuario=self.usuario, obra=self.obra, tema=self.tema,
        )
        self.assertEqual(suscripcion.nivel, 'tema')

    def test_no_permite_unidad_y_tema_a_la_vez(self):
        suscripcion = Suscripcion(
            usuario=self.usuario, obra=self.obra, unidad=self.unidad, tema=self.tema,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                suscripcion.save()

    def test_clean_rechaza_unidad_de_otra_obra(self):
        suscripcion = Suscripcion(
            usuario=self.usuario, obra=self.obra, unidad=self.unidad_otra_obra,
        )
        with self.assertRaises(ValidationError):
            suscripcion.clean()

    def test_clean_rechaza_tema_de_otra_obra(self):
        suscripcion = Suscripcion(
            usuario=self.usuario, obra=self.obra, tema=self.tema_otra_obra,
        )
        with self.assertRaises(ValidationError):
            suscripcion.clean()


class ServiciosSuscripcionTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('lector', password='x')
        self.obra = Obra.objects.create(titulo='Serie', slug='serie')

    def test_crear_suscripcion_es_idempotente(self):
        primera = crear_suscripcion(self.usuario, self.obra)
        segunda = crear_suscripcion(self.usuario, self.obra)
        self.assertEqual(primera.pk, segunda.pk)
        self.assertEqual(Suscripcion.objects.count(), 1)

    def test_crear_suscripcion_rechaza_unidad_y_tema_simultaneos(self):
        unidad = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='arco', nombre='Arco', orden_local=1,
        )
        tema = TemaTransversal.objects.create(obra=self.obra, nombre='Tema')
        with self.assertRaises(ValueError):
            crear_suscripcion(self.usuario, self.obra, unidad=unidad, tema=tema)

    def test_eliminar_suscripcion(self):
        crear_suscripcion(self.usuario, self.obra)
        eliminar_suscripcion(self.usuario, self.obra)
        self.assertEqual(Suscripcion.objects.count(), 0)

    def test_marcar_visto_actualiza_ultima_visita(self):
        suscripcion = crear_suscripcion(self.usuario, self.obra)
        self.assertIsNone(suscripcion.ultima_visita)
        marcar_visto(suscripcion)
        suscripcion.refresh_from_db()
        self.assertIsNotNone(suscripcion.ultima_visita)


class PostsNoLeidosTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('autor', password='x')
        self.lector = User.objects.create_user('lector', password='x')
        self.obra = Obra.objects.create(titulo='Serie', slug='serie')
        self.arco = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='arco', nombre='Arco', orden_local=1,
        )
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, padre=self.arco, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, padre=self.arco, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.obra.recalcular_orden()
        for u in (self.arco, self.e1, self.e2):
            u.refresh_from_db()

    def _post(self, referencia):
        return Post.objects.create(
            author=self.autor, obra=self.obra, text='contenido',
            referencia_narrativa=referencia, frontera_spoiler=referencia,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_suscripcion_a_obra_cuenta_todos_los_posts(self):
        suscripcion = crear_suscripcion(self.lector, self.obra)
        self._post(self.e1)
        self._post(self.e2)
        self.assertEqual(posts_no_leidos_count(suscripcion), 2)

    def test_suscripcion_a_unidad_incluye_hijos_por_rango(self):
        suscripcion = crear_suscripcion(self.lector, self.obra, unidad=self.arco)
        self._post(self.e1)
        self._post(self.e2)
        self.assertEqual(posts_no_leidos_count(suscripcion), 2)

    def test_suscripcion_a_unidad_excluye_fuera_de_rango(self):
        otro_arco = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='arco', nombre='Otro arco', orden_local=2,
        )
        e3 = UnidadNarrativa.objects.create(
            obra=self.obra, padre=otro_arco, tipo='episodio', nombre='E3', orden_local=1,
        )
        self.obra.recalcular_orden()
        otro_arco.refresh_from_db()
        e3.refresh_from_db()

        suscripcion = crear_suscripcion(self.lector, self.obra, unidad=self.arco)
        self._post(self.e1)
        self._post(e3)
        self.assertEqual(posts_no_leidos_count(suscripcion), 1)

    def test_marcar_visto_excluye_posts_anteriores(self):
        suscripcion = crear_suscripcion(self.lector, self.obra)
        self._post(self.e1)
        marcar_visto(suscripcion)
        self._post(self.e2)
        self.assertEqual(posts_no_leidos_count(suscripcion), 1)