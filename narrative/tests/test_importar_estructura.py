import os
import tempfile
from datetime import date
from io import StringIO

import yaml
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from ..models import Obra, UnidadNarrativa, ExternalId, TemaTransversal


class EstructuraTestCase(TestCase):
    """Base: obra anclada por ExternalId y YAML temporales con limpieza automática."""

    titulo = slug = tipo = source = external_id = None

    def setUp(self):
        self.obra = Obra.objects.create(titulo=self.titulo, slug=self.slug, tipo=self.tipo)
        ExternalId.objects.create(source=self.source, external_id=self.external_id, obra=self.obra)

    def escribir_yaml(self, data):
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
        yaml.dump(data, f, allow_unicode=True)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def estructura(self, nodos, **extra):
        return self.escribir_yaml({
            'obra_external_id': {'source': self.source, 'external_id': self.external_id},
            'nodos': nodos,
            **extra,
        })

    def importar(self, ruta, **opciones):
        salida = StringIO()
        call_command('importar_estructura', ruta, stdout=salida, **opciones)
        return salida.getvalue()

    def contar(self, tipo, **filtros):
        return UnidadNarrativa.objects.filter(obra=self.obra, tipo=tipo, **filtros).count()


class AnimeConEpisodiosPreviosTests(EstructuraTestCase):
    """Fase A ya trajo episodios reales antes de correr Fase B."""

    titulo, slug, tipo = 'Serie X', 'serie-x', Obra.TIPO_SERIE
    source, external_id = 'jikan', '999'

    def setUp(self):
        super().setUp()
        for n in range(1, 7):
            UnidadNarrativa.objects.create(
                obra=self.obra, padre=None, tipo='episodio', nombre=f'Ep {n}', orden_local=n,
            )

    def test_reagrupa_episodios_en_arcos_y_recalcula_orden(self):
        self.importar(self.estructura([
            {'tipo': 'arco', 'nombre': 'Arco 1', 'orden_local': 1, 'vincular_episodios': [1, 3]},
            {'tipo': 'arco', 'nombre': 'Arco 2', 'orden_local': 2, 'vincular_episodios': [4, 6]},
        ]))

        arco1 = UnidadNarrativa.objects.get(obra=self.obra, nombre='Arco 1')
        arco2 = UnidadNarrativa.objects.get(obra=self.obra, nombre='Arco 2')
        self.assertEqual(UnidadNarrativa.objects.filter(padre=arco1).count(), 3)
        self.assertEqual(UnidadNarrativa.objects.filter(padre=arco2).count(), 3)
        self.assertEqual(self.contar('episodio'), 6)
        self.assertEqual(arco1.orden_inicio, 1)
        self.assertEqual(arco2.orden_fin, 6)

    def test_es_idempotente_al_relanzar(self):
        ruta = self.estructura([
            {'tipo': 'arco', 'nombre': 'Arco 1', 'orden_local': 1, 'vincular_episodios': [1, 6]},
        ])
        self.importar(ruta)
        self.importar(ruta)

        self.assertEqual(self.contar('arco'), 1)
        self.assertEqual(self.contar('episodio'), 6)

    def test_falla_si_la_obra_no_se_ha_importado(self):
        ruta = self.escribir_yaml({
            'obra_external_id': {'source': 'jikan', 'external_id': 'no-existe'},
            'nodos': [],
        })
        with self.assertRaises(CommandError):
            self.importar(ruta)


class AnimeSinEpisodiosPreviosTests(EstructuraTestCase):
    """Fase B antes que Fase A (Jikan caído): crea episodios placeholder."""

    titulo, slug, tipo = 'Serie Y', 'serie-y', Obra.TIPO_SERIE
    source, external_id = 'jikan', '777'

    def test_crea_episodios_placeholder_cuando_no_existen(self):
        self.importar(self.estructura([
            {'tipo': 'arco', 'nombre': 'Arco 1', 'orden_local': 1, 'vincular_episodios': [1, 4]},
        ]))

        arco = UnidadNarrativa.objects.get(obra=self.obra, nombre='Arco 1')
        episodios = UnidadNarrativa.objects.filter(obra=self.obra, tipo='episodio', padre=arco)
        self.assertEqual(
            sorted(episodios.values_list('nombre', flat=True)),
            ['Episodio 1', 'Episodio 2', 'Episodio 3', 'Episodio 4'],
        )

    def test_rango_abierto_sin_hasta_episodio_no_crea_nada(self):
        salida = self.importar(self.estructura([
            {'tipo': 'arco', 'nombre': 'Arco Final', 'orden_local': 1, 'vincular_episodios': [1156, None]},
        ]))
        self.assertEqual(self.contar('episodio'), 0)
        self.assertIn('rango abierto', salida)

    def test_rango_abierto_con_hasta_episodio_lo_cierra(self):
        self.importar(self.estructura([
            {'tipo': 'arco', 'nombre': 'Arco Final', 'orden_local': 1, 'vincular_episodios': [10, None]},
        ]), hasta_episodio=12)
        self.assertEqual(self.contar('episodio'), 3)


class MangaTests(EstructuraTestCase):
    titulo, slug, tipo = 'Manga X', 'manga-x', Obra.TIPO_MANGA
    source, external_id = 'jikan', '888'

    def test_crea_capitulos_desde_rango_cerrado(self):
        self.importar(self.estructura([
            {'tipo': 'arco', 'nombre': 'Arco Piloto', 'orden_local': 1, 'vincular_capitulos': [1, 5]},
        ]))
        self.assertEqual(self.contar('capitulo'), 5)

    def test_rango_abierto_sin_hasta_capitulo_no_crea_nada(self):
        salida = self.importar(self.estructura([
            {'tipo': 'arco', 'nombre': 'Arco Abierto', 'orden_local': 1, 'vincular_capitulos': [1, None]},
        ]))
        self.assertEqual(self.contar('capitulo'), 0)
        self.assertIn('rango abierto', salida)

    def test_rango_abierto_con_hasta_capitulo_lo_cierra(self):
        self.importar(self.estructura([
            {'tipo': 'arco', 'nombre': 'Arco Abierto', 'orden_local': 1, 'vincular_capitulos': [10, None]},
        ]), hasta_capitulo=12)
        self.assertEqual(self.contar('capitulo'), 3)

    def test_temas_transversales_vincula_capitulos_por_rango(self):
        self.importar(self.estructura(
            [{'tipo': 'arco', 'nombre': 'Arco', 'orden_local': 1, 'vincular_capitulos': [1, 10]}],
            temas_transversales=[
                {'nombre': 'Minihistoria X', 'tipo': 'minihistoria', 'rango_capitulos': [3, 5], 'revisar': True},
            ],
        ))

        tema = TemaTransversal.objects.get(obra=self.obra, nombre='Minihistoria X')
        self.assertEqual(tema.tipo, TemaTransversal.TIPO_MINIHISTORIA)
        self.assertEqual(tema.unidades.count(), 3)


class FechasVolumenTests(EstructuraTestCase):
    """Fecha de capítulo aproximada por reparto proporcional de volúmenes."""

    titulo, slug, tipo = 'Manga Z', 'manga-z', Obra.TIPO_MANGA
    source, external_id = 'jikan', '555'

    def setUp(self):
        super().setUp()
        self.ruta_fechas = self.escribir_yaml({1: '2000-01-01', 2: '2000-02-01', 3: '2000-03-01'})

    def _arco(self, capitulos, volumenes):
        return self.estructura([{
            'tipo': 'arco', 'nombre': 'Arco', 'orden_local': 1,
            'vincular_capitulos': capitulos, 'volumenes': volumenes,
        }])

    def _fechas(self):
        return set(UnidadNarrativa.objects.filter(
            obra=self.obra, tipo='capitulo',
        ).values_list('fecha', flat=True))

    def test_reparte_capitulos_entre_volumenes_proporcionalmente(self):
        self.importar(self._arco([1, 9], [1, 3]), fechas_volumen=self.ruta_fechas)

        fechas = {
            u.orden_local: u.fecha
            for u in UnidadNarrativa.objects.filter(obra=self.obra, tipo='capitulo')
        }
        self.assertEqual([fechas[n] for n in (1, 2, 3)], [date(2000, 1, 1)] * 3)
        self.assertEqual([fechas[n] for n in (4, 5, 6)], [date(2000, 2, 1)] * 3)
        self.assertEqual([fechas[n] for n in (7, 8, 9)], [date(2000, 3, 1)] * 3)

    def test_volumen_unico_asigna_la_misma_fecha_a_todos(self):
        self.importar(self._arco([1, 5], [2, 2]), fechas_volumen=self.ruta_fechas)
        self.assertEqual(self._fechas(), {date(2000, 2, 1)})

    def test_sin_fechas_volumen_no_asigna_fecha(self):
        self.importar(self._arco([1, 3], [1, 1]))
        self.assertEqual(self._fechas(), {None})


class FechaDirectaTests(EstructuraTestCase):
    """Curación manual sin Jikan: fecha real indicada en el propio nodo."""

    titulo, slug, tipo = 'Star Wars', 'star-wars', Obra.TIPO_SERIE
    source, external_id = ExternalId.SOURCE_MANUAL, 'star-wars'

    def test_asigna_fecha_directa_del_nodo(self):
        self.importar(self.estructura([
            {'tipo': 'pelicula', 'nombre': 'Episodio IV', 'orden_local': 1, 'fecha': '1977-05-25'},
            {'tipo': 'pelicula', 'nombre': 'Episodio V', 'orden_local': 2, 'fecha': '1980-05-21'},
        ]))

        ep4 = UnidadNarrativa.objects.get(obra=self.obra, nombre='Episodio IV')
        ep5 = UnidadNarrativa.objects.get(obra=self.obra, nombre='Episodio V')
        self.assertEqual(ep4.fecha, date(1977, 5, 25))
        self.assertEqual(ep5.fecha, date(1980, 5, 21))
        self.assertEqual(ep4.orden_inicio, 1)
        self.assertEqual(ep5.orden_inicio, 2)


class ColisionEntrePartesTests(EstructuraTestCase):
    """Regresión Naruto: orden_local es único por Obra; rangos solapados
    entre Partes son un error de curación, no algo a absorber."""

    titulo, slug, tipo = 'Serie Doble', 'serie-doble', Obra.TIPO_SERIE
    source, external_id = ExternalId.SOURCE_MANUAL, 'serie-doble'

    def _dos_partes(self, rango_a, rango_b):
        return self.estructura([
            {'tipo': 'parte', 'nombre': 'Parte A', 'orden_local': 1, 'hijos': [
                {'tipo': 'temporada', 'nombre': 'T1', 'orden_local': 1, 'vincular_episodios': rango_a},
            ]},
            {'tipo': 'parte', 'nombre': 'Parte B', 'orden_local': 2, 'hijos': [
                {'tipo': 'temporada', 'nombre': 'T1', 'orden_local': 1, 'vincular_episodios': rango_b},
            ]},
        ])

    def test_rangos_solapados_entre_partes_no_deben_compartir_episodios(self):
        """Documenta el mecanismo: Parte B adopta los episodios de Parte A (10, no 20)."""
        self.importar(self._dos_partes([1, 10], [1, 10]))
        self.assertEqual(self.contar('episodio'), 10)

    def test_rangos_correlativos_entre_partes_no_colisionan(self):
        """Forma correcta: numeración continua (Shippūden empieza en 221)."""
        self.importar(self._dos_partes([1, 10], [11, 20]))
        self.assertEqual(self.contar('episodio'), 20)