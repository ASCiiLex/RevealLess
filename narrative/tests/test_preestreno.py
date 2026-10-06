from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, UnidadNarrativa
from narrative.services import (
    UNIDAD_PREVIA_NOMBRE,
    actualizar_progreso,
    asegurar_unidad_previa,
)
from posts.models import Post


class UnidadPreviaTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo='Por estrenar', slug='por-estrenar')

    def test_crea_una_unica_unidad_previa(self):
        unidad = asegurar_unidad_previa(self.obra)
        self.assertEqual(unidad.nombre, UNIDAD_PREVIA_NOMBRE)
        self.assertIsNone(asegurar_unidad_previa(self.obra))
        self.assertEqual(self.obra.unidades.count(), 1)

    def test_no_crea_nada_si_la_obra_ya_tiene_unidades(self):
        UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='Uno', orden_local=1)
        self.assertIsNone(asegurar_unidad_previa(self.obra))
        self.assertFalse(self.obra.unidades.filter(nombre=UNIDAD_PREVIA_NOMBRE).exists())

    def test_queda_la_primera_al_cargar_episodios(self):
        previa = asegurar_unidad_previa(self.obra)
        UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='Piloto', orden_local=1)
        self.obra.recalcular_orden()
        self.assertEqual(self.obra.unidades.order_by('orden_inicio').first(), previa)


class PreestrenoFlujoTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autora = User.objects.create_user('autora', password='x')
        self.lectora = User.objects.create_user('lectora', password='x')
        self.obra = Obra.objects.create(titulo='Por estrenar', slug='por-estrenar')

    def _previa_desde_api(self, usuario):
        self.client.force_authenticate(user=usuario)
        response = self.client.get(reverse('narrative_api_progreso', args=[self.obra.slug]))
        self.assertEqual(response.status_code, 200)
        return response.data['unidades']

    def test_el_arbol_de_progreso_ofrece_la_unidad_previa(self):
        unidades = self._previa_desde_api(self.autora)
        self.assertEqual([u['nombre'] for u in unidades], [UNIDAD_PREVIA_NOMBRE])
        # Una segunda consulta no la duplica.
        self.assertEqual(len(self._previa_desde_api(self.lectora)), 1)

    def test_se_publica_y_se_lee_antes_del_estreno(self):
        previa_id = self._previa_desde_api(self.autora)[0]['id']
        previa = UnidadNarrativa.objects.get(id=previa_id)
        actualizar_progreso(self.autora, self.obra, previa)

        response = self.client.post(
            reverse('posts_api_create', args=[self.obra.slug]),
            {'text': 'Qué ganas de que se estrene', 'referencia_narrativa': previa_id, 'frontera_spoiler': previa_id},
        )
        self.assertEqual(response.status_code, 201)
        post = Post.objects.get(id=response.data['id'])

        actualizar_progreso(self.lectora, self.obra, previa)
        self.assertIn(post, Post.objects.visible_for(self.lectora))

        # Con los episodios ya cargados, el post de preestreno sigue visible.
        UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='Piloto', orden_local=1)
        self.obra.recalcular_orden()
        post.refresh_from_db()
        self.assertIn(post, Post.objects.visible_for(self.lectora))