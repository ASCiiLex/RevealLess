from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from narrative.models import ProgresoUsuario, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from ..models import Post
from .utils import crear_obra


class ClasificacionNarrativaEnPostTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('autor', password='x')
        self.obra, (self.e1, self.e2) = crear_obra('serie', 2)
        _, (self.unidad_otra_obra,) = crear_obra('otra')

    def _post(self, **kwargs):
        campos = dict(
            author=self.autor, obra=self.obra, text='hola',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        campos.update(kwargs)
        return Post(**campos)

    def _assert_integrity_error(self, post):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                post.save()

    def test_frontera_orden_se_calcula_al_guardar(self):
        post = self._post(frontera_spoiler=self.e2)
        post.save()
        self.assertEqual(post.frontera_orden, self.e2.orden_fin)

    def test_heredado_post_no_valido_en_post(self):
        self._assert_integrity_error(self._post(frontera_origen=ClasificacionNarrativa.ORIGEN_HEREDADO_POST))

    def test_frontera_spoiler_obligatoria_en_post(self):
        self._assert_integrity_error(self._post(frontera_spoiler=None))

    def test_clean_rechaza_referencia_de_otra_obra(self):
        with self.assertRaises(ValidationError):
            self._post(referencia_narrativa=self.unidad_otra_obra).clean()

    def test_clean_rechaza_frontera_de_otra_obra(self):
        with self.assertRaises(ValidationError):
            self._post(frontera_spoiler=self.unidad_otra_obra).clean()

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