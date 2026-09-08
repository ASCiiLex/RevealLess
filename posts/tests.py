from django.contrib.auth.models import User, AnonymousUser
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.test import TestCase

from narrative.models import Obra, UnidadNarrativa, ProgresoUsuario, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from .models import Post


class ClasificacionNarrativaEnPostTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('autor', password='x')
        self.obra = Obra.objects.create(titulo='Serie', slug='serie')
        self.otra_obra = Obra.objects.create(titulo='Otra', slug='otra')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()
        self.unidad_otra_obra = UnidadNarrativa.objects.create(
            obra=self.otra_obra, tipo='episodio', nombre='X1', orden_local=1,
        )

    def _post(self, **kwargs):
        defaults = dict(
            author=self.autor, obra=self.obra, text='hola',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        defaults.update(kwargs)
        return Post(**defaults)

    def test_frontera_orden_se_calcula_al_guardar(self):
        post = self._post(frontera_spoiler=self.e2)
        post.save()
        self.assertEqual(post.frontera_orden, self.e2.orden_fin)

    def test_heredado_post_no_valido_en_post(self):
        post = self._post(frontera_origen=ClasificacionNarrativa.ORIGEN_HEREDADO_POST)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                post.save()

    def test_frontera_spoiler_obligatoria_en_post(self):
        post = self._post(frontera_spoiler=None)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                post.save()

    def test_clean_rechaza_referencia_de_otra_obra(self):
        post = self._post(referencia_narrativa=self.unidad_otra_obra)
        with self.assertRaises(ValidationError):
            post.clean()

    def test_clean_rechaza_frontera_de_otra_obra(self):
        post = self._post(frontera_spoiler=self.unidad_otra_obra)
        with self.assertRaises(ValidationError):
            post.clean()

    def test_frontera_fallback_queda_congelada_ante_avance_posterior(self):
        actualizar_progreso(self.autor, self.obra, self.e1)
        progreso = ProgresoUsuario.objects.get(usuario=self.autor, obra=self.obra)

        post = self._post(
            frontera_spoiler=progreso.unidad_actual,
            frontera_origen=ClasificacionNarrativa.ORIGEN_FALLBACK,
        )
        post.save()
        frontera_original = post.frontera_orden

        actualizar_progreso(self.autor, self.obra, self.e2)

        post.refresh_from_db()
        self.assertEqual(post.frontera_orden, frontera_original)


class VisibilidadPostTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('autor', password='x')
        self.lector_avanzado = User.objects.create_user('avanzado', password='x')
        self.lector_atrasado = User.objects.create_user('atrasado', password='x')

        self.obra = Obra.objects.create(titulo='Serie', slug='serie')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.e2 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E2', orden_local=2)
        self.e3 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E3', orden_local=3)
        self.obra.recalcular_orden()
        for u in (self.e1, self.e2, self.e3):
            u.refresh_from_db()

        actualizar_progreso(self.autor, self.obra, self.e2)
        actualizar_progreso(self.lector_avanzado, self.obra, self.e3)
        actualizar_progreso(self.lector_atrasado, self.obra, self.e1)

        # El autor va por E2 pero publica sobre algo que exige E3
        # (caso legítimo: información externa, ver reglas de dominio 13.3).
        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='spoiler gordo',
            referencia_narrativa=self.e1, frontera_spoiler=self.e3,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_lector_avanzado_ve_el_post(self):
        self.assertIn(self.post, Post.objects.visible_for(self.lector_avanzado))

    def test_lector_atrasado_no_ve_el_post(self):
        self.assertNotIn(self.post, Post.objects.visible_for(self.lector_atrasado))

    def test_autor_ve_su_propio_post_aunque_no_haya_llegado(self):
        self.assertIn(self.post, Post.objects.visible_for(self.autor))

    def test_usuario_anonimo_no_ve_nada(self):
        visibles = Post.objects.visible_for(AnonymousUser())
        self.assertFalse(visibles.exists())