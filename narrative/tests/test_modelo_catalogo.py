from django.db import IntegrityError, transaction
from django.test import TestCase

from ..models import Obra, UnidadNarrativa, Categoria, ExternalId, TemaTransversal
from ..serializers import UnidadNarrativaSerializer


class CategoriaTests(TestCase):
    def test_nombre_unico(self):
        Categoria.objects.create(nombre='anime')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Categoria.objects.create(nombre='anime')

    def test_obra_puede_tener_varias_categorias(self):
        obra = Obra.objects.create(titulo='One Piece', slug='one-piece')
        anime = Categoria.objects.create(nombre='anime')
        accion = Categoria.objects.create(nombre='acción')
        obra.categorias.set([anime, accion])
        self.assertEqual(obra.categorias.count(), 2)

    def test_categoria_no_afecta_frontera_orden(self):
        """Categoria es cosmética: sin vía para influir en frontera_orden."""
        obra = Obra.objects.create(titulo='Serie', slug='serie-cat')
        categoria = Categoria.objects.create(nombre='series')
        obra.categorias.add(categoria)
        self.assertFalse(hasattr(categoria, 'frontera_orden'))


class UnidadNarrativaSerializerTests(TestCase):
    def test_incluye_padre_para_reconstruir_jerarquia_en_frontend(self):
        obra = Obra.objects.create(titulo='Serie D', slug='serie-d')
        saga = UnidadNarrativa.objects.create(
            obra=obra, tipo='saga', nombre='Saga 1', orden_local=1,
        )
        arco = UnidadNarrativa.objects.create(
            obra=obra, padre=saga, tipo='arco', nombre='Arco 1', orden_local=1,
        )

        self.assertIsNone(UnidadNarrativaSerializer(saga).data['padre'])
        self.assertEqual(UnidadNarrativaSerializer(arco).data['padre'], saga.id)


class ExternalIdTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo='Serie E', slug='serie-e')
        self.unidad = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )

    def _assert_integrity_error(self, **kwargs):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ExternalId.objects.create(**kwargs)

    def test_exige_un_solo_destino(self):
        self._assert_integrity_error(source='jikan', external_id='1')

    def test_no_permite_ambos_destinos_a_la_vez(self):
        self._assert_integrity_error(
            source='jikan', external_id='1', obra=self.obra, unidad=self.unidad,
        )

    def test_unicidad_por_fuente_y_obra(self):
        ExternalId.objects.create(source='jikan', external_id='21', obra=self.obra)
        self._assert_integrity_error(source='jikan', external_id='99', obra=self.obra)

    def test_unicidad_por_fuente_y_unidad(self):
        ExternalId.objects.create(source='jikan', external_id='1', unidad=self.unidad)
        self._assert_integrity_error(source='jikan', external_id='2', unidad=self.unidad)

    def test_distintas_obras_pueden_tener_externalid_propio(self):
        otra_obra = Obra.objects.create(titulo='Serie F', slug='serie-f')
        ExternalId.objects.create(source='jikan', external_id='21', obra=self.obra)
        ExternalId.objects.create(source='jikan', external_id='13', obra=otra_obra)
        self.assertEqual(ExternalId.objects.count(), 2)


class TemaTransversalTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo='Serie G', slug='serie-g')
        self.capitulo = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='capitulo', nombre='Cap 1', orden_local=1,
        )

    def test_tipo_por_defecto_es_tematico(self):
        tema = TemaTransversal.objects.create(obra=self.obra, nombre='Frutas del diablo')
        self.assertEqual(tema.tipo, TemaTransversal.TIPO_TEMATICO)

    def test_minihistoria_puede_vincular_unidades(self):
        tema = TemaTransversal.objects.create(
            obra=self.obra, nombre='Minihistoria X', tipo=TemaTransversal.TIPO_MINIHISTORIA,
        )
        tema.unidades.add(self.capitulo)
        self.assertEqual(tema.unidades.count(), 1)

    def test_unidades_no_participa_en_frontera_orden(self):
        """Vincular una unidad a un tema no toca orden_inicio/orden_fin."""
        self.obra.recalcular_orden()
        self.capitulo.refresh_from_db()
        orden_previo = self.capitulo.orden_inicio

        tema = TemaTransversal.objects.create(
            obra=self.obra, nombre='Tema', tipo=TemaTransversal.TIPO_MINIHISTORIA,
        )
        tema.unidades.add(self.capitulo)
        self.capitulo.refresh_from_db()

        self.assertEqual(self.capitulo.orden_inicio, orden_previo)