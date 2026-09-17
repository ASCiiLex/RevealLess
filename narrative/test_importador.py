import os
import tempfile
from datetime import date
from io import StringIO
from unittest.mock import patch, Mock

import yaml
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from .models import Obra, UnidadNarrativa, ExternalId, TemaTransversal
from .services import jikan_client


def _escribir_yaml(data):
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
    yaml.dump(data, f, allow_unicode=True)
    f.close()
    return f.name


ANIME_DATA = {
    'title': 'One Piece',
    'type': 'TV',
    'synopsis': 'Un pirata busca un tesoro.',
    'aired': {'from': '1999-10-20T00:00:00+00:00'},
    'studios': [{'name': 'Toei Animation'}],
    'episodes': 3,
}

MANGA_DATA = {
    'title': 'One Piece',
    'synopsis': 'Un pirata busca un tesoro.',
    'published': {'from': '1997-07-22T00:00:00+00:00'},
    'authors': [{'name': 'Eiichiro Oda'}],
}


class ImportarCatalogoAnimeTests(TestCase):
    @patch('narrative.services.jikan_client.get_relations', return_value=[])
    @patch('narrative.services.jikan_client.get_anime_episodes')
    @patch('narrative.services.jikan_client.get_anime', return_value=ANIME_DATA)
    def test_crea_obra_y_episodios(self, mock_anime, mock_episodios, mock_relations):
        mock_episodios.return_value = (
            [
                {'mal_id': 1, 'title': 'Romance Dawn', 'aired': '1999-10-20'},
                {'mal_id': 2, 'title': 'That Girl', 'aired': '1999-10-27'},
                {'mal_id': 3, 'title': 'Morgan', 'aired': '1999-11-03'},
            ],
            [],
        )
        call_command('importar_catalogo', tipo='anime', external_id=21, stdout=StringIO())

        obra = Obra.objects.get(tipo=Obra.TIPO_SERIE)
        self.assertEqual(obra.titulo, 'One Piece')
        self.assertEqual(obra.autor, 'Estudio: Toei Animation')
        self.assertTrue(ExternalId.objects.filter(source='jikan', external_id='21', obra=obra).exists())

        episodios = UnidadNarrativa.objects.filter(obra=obra, tipo='episodio')
        self.assertEqual(episodios.count(), 3)
        for ep_id in (1, 2, 3):
            self.assertTrue(ExternalId.objects.filter(source='jikan', external_id=str(ep_id)).exists())

    @patch('narrative.services.jikan_client.get_relations', return_value=[])
    @patch('narrative.services.jikan_client.get_anime_episodes', return_value=([], []))
    @patch('narrative.services.jikan_client.get_anime', return_value=ANIME_DATA)
    def test_idempotente_no_duplica_obra_ni_externalid(self, mock_anime, mock_episodios, mock_relations):
        call_command('importar_catalogo', tipo='anime', external_id=21, stdout=StringIO())
        call_command('importar_catalogo', tipo='anime', external_id=21, stdout=StringIO())

        self.assertEqual(Obra.objects.filter(tipo=Obra.TIPO_SERIE).count(), 1)
        self.assertEqual(ExternalId.objects.filter(source='jikan', external_id='21').count(), 1)

    @patch('narrative.services.jikan_client.get_relations', return_value=[])
    @patch('narrative.services.jikan_client.get_anime_episodes', return_value=([], []))
    @patch('narrative.services.jikan_client.get_anime')
    def test_mapea_tipo_jikan_movie_a_pelicula(self, mock_anime, mock_episodios, mock_relations):
        mock_anime.return_value = {**ANIME_DATA, 'type': 'Movie', 'title': 'One Piece: La Película'}
        call_command('importar_catalogo', tipo='anime', external_id=1, stdout=StringIO())

        obra = Obra.objects.get(tipo=Obra.TIPO_PELICULA)
        self.assertEqual(obra.titulo, 'One Piece: La Película')

    @patch('narrative.services.jikan_client.get_relations', return_value=[])
    @patch('narrative.services.jikan_client.get_anime_episodes', return_value=([], []))
    @patch('narrative.services.jikan_client.get_anime')
    def test_evita_colision_de_slug_con_manga_del_mismo_titulo(self, mock_get_anime, mock_episodios, mock_relations):
        mock_get_anime.return_value = ANIME_DATA
        call_command('importar_catalogo', tipo='anime', external_id=21, stdout=StringIO())

        with patch('narrative.services.jikan_client.get_manga', return_value=MANGA_DATA):
            call_command('importar_catalogo', tipo='manga', external_id=13, stdout=StringIO())

        slugs = set(Obra.objects.values_list('slug', flat=True))
        self.assertEqual(len(slugs), 2)  # dos Obras, dos slugs distintos

    @patch('narrative.services.jikan_client.get_relations', return_value=[])
    @patch('narrative.services.jikan_client.get_anime_episodes')
    @patch('narrative.services.jikan_client.get_anime', return_value=ANIME_DATA)
    def test_adopta_placeholder_creado_por_fase_b_en_vez_de_duplicar(self, mock_anime, mock_episodios, mock_relations):
        obra = Obra.objects.create(titulo='One Piece', slug='one-piece', tipo=Obra.TIPO_SERIE)
        ExternalId.objects.create(source='jikan', external_id='21', obra=obra)
        arco = UnidadNarrativa.objects.create(
            obra=obra, tipo='arco', nombre='Arco de Romance Dawn', orden_local=1,
        )
        placeholder = UnidadNarrativa.objects.create(
            obra=obra, padre=arco, tipo='episodio', nombre='Episodio 1', orden_local=1,
        )
        self.assertEqual(UnidadNarrativa.objects.filter(obra=obra, tipo='episodio').count(), 1)

        mock_episodios.return_value = (
            [{'mal_id': 1, 'title': 'Romance Dawn', 'aired': '1999-10-20'}],
            [],
        )
        call_command('importar_catalogo', tipo='anime', external_id=21, stdout=StringIO())

        # Sigue siendo UNA sola unidad, la misma fila (mismo pk), ahora con
        # datos reales, y sin perder el padre que ya tenía.
        self.assertEqual(UnidadNarrativa.objects.filter(obra=obra, tipo='episodio').count(), 1)
        placeholder.refresh_from_db()
        self.assertEqual(placeholder.nombre, 'Romance Dawn')
        self.assertEqual(placeholder.padre_id, arco.id)
        self.assertTrue(ExternalId.objects.filter(source='jikan', external_id='1', unidad=placeholder).exists())


class ImportarCatalogoMangaTests(TestCase):
    @patch('narrative.services.jikan_client.get_relations', return_value=[])
    @patch('narrative.services.jikan_client.get_manga', return_value=MANGA_DATA)
    def test_crea_obra_sin_episodios_ni_capitulos(self, mock_manga, mock_relations):
        call_command('importar_catalogo', tipo='manga', external_id=13, stdout=StringIO())

        obra = Obra.objects.get(tipo=Obra.TIPO_MANGA)
        self.assertEqual(obra.autor, 'Eiichiro Oda')
        self.assertEqual(UnidadNarrativa.objects.filter(obra=obra).count(), 0)

    @patch('narrative.services.jikan_client.get_relations')
    @patch('narrative.services.jikan_client.get_manga', return_value=MANGA_DATA)
    def test_fallo_en_relations_no_aborta_el_comando(self, mock_manga, mock_relations):
        """Regresión: relations puede fallar (Jikan/MAL caído) sin que se
        pierda la Obra ya creada — ya estaba protegido, se confirma aquí."""
        mock_relations.side_effect = jikan_client.JikanError('504 simulado')
        call_command('importar_catalogo', tipo='manga', external_id=13, stdout=StringIO())
        self.assertTrue(Obra.objects.filter(tipo=Obra.TIPO_MANGA).exists())


class ImportarEstructuraAnimeConEpisodiosPreviosTests(TestCase):
    """Escenario: Fase A ya trajo episodios reales antes de correr Fase B."""

    def setUp(self):
        self.obra = Obra.objects.create(titulo='Serie X', slug='serie-x', tipo=Obra.TIPO_SERIE)
        ExternalId.objects.create(source='jikan', external_id='999', obra=self.obra)
        for n in range(1, 7):
            UnidadNarrativa.objects.create(
                obra=self.obra, padre=None, tipo='episodio', nombre=f'Ep {n}', orden_local=n,
            )
        self.ruta = None

    def tearDown(self):
        if self.ruta and os.path.exists(self.ruta):
            os.unlink(self.ruta)

    def test_reagrupa_episodios_en_arcos_y_recalcula_orden(self):
        self.ruta = _escribir_yaml({
            'obra_external_id': {'source': 'jikan', 'external_id': 999},
            'nodos': [
                {'tipo': 'arco', 'nombre': 'Arco 1', 'orden_local': 1, 'vincular_episodios': [1, 3]},
                {'tipo': 'arco', 'nombre': 'Arco 2', 'orden_local': 2, 'vincular_episodios': [4, 6]},
            ],
        })
        call_command('importar_estructura', self.ruta, stdout=StringIO())

        arco1 = UnidadNarrativa.objects.get(obra=self.obra, nombre='Arco 1')
        arco2 = UnidadNarrativa.objects.get(obra=self.obra, nombre='Arco 2')
        self.assertEqual(UnidadNarrativa.objects.filter(padre=arco1).count(), 3)
        self.assertEqual(UnidadNarrativa.objects.filter(padre=arco2).count(), 3)
        # No se duplicó ninguno: siguen siendo 6 episodios en total.
        self.assertEqual(UnidadNarrativa.objects.filter(obra=self.obra, tipo='episodio').count(), 6)
        self.assertEqual(arco1.orden_inicio, 1)
        self.assertEqual(arco2.orden_fin, 6)

    def test_es_idempotente_al_relanzar(self):
        self.ruta = _escribir_yaml({
            'obra_external_id': {'source': 'jikan', 'external_id': 999},
            'nodos': [{'tipo': 'arco', 'nombre': 'Arco 1', 'orden_local': 1, 'vincular_episodios': [1, 6]}],
        })
        call_command('importar_estructura', self.ruta, stdout=StringIO())
        call_command('importar_estructura', self.ruta, stdout=StringIO())

        self.assertEqual(UnidadNarrativa.objects.filter(obra=self.obra, tipo='arco').count(), 1)
        self.assertEqual(UnidadNarrativa.objects.filter(obra=self.obra, tipo='episodio').count(), 6)

    def test_falla_si_la_obra_no_se_ha_importado(self):
        self.ruta = _escribir_yaml({
            'obra_external_id': {'source': 'jikan', 'external_id': 'no-existe'},
            'nodos': [],
        })
        with self.assertRaises(CommandError):
            call_command('importar_estructura', self.ruta, stdout=StringIO())


class ImportarEstructuraAnimeSinEpisodiosPreviosTests(TestCase):
    """Escenario nuevo: Fase B corre ANTES de que Jikan haya traído nada
    (Jikan caído). Debe crear los episodios como placeholder, no limitarse
    a avisar de que no encuentra nada que reasignar."""

    def setUp(self):
        self.obra = Obra.objects.create(titulo='Serie Y', slug='serie-y', tipo=Obra.TIPO_SERIE)
        ExternalId.objects.create(source='jikan', external_id='777', obra=self.obra)
        self.ruta = None

    def tearDown(self):
        if self.ruta and os.path.exists(self.ruta):
            os.unlink(self.ruta)

    def test_crea_episodios_placeholder_cuando_no_existen(self):
        self.ruta = _escribir_yaml({
            'obra_external_id': {'source': 'jikan', 'external_id': 777},
            'nodos': [{'tipo': 'arco', 'nombre': 'Arco 1', 'orden_local': 1, 'vincular_episodios': [1, 4]}],
        })
        call_command('importar_estructura', self.ruta, stdout=StringIO())

        arco = UnidadNarrativa.objects.get(obra=self.obra, nombre='Arco 1')
        episodios = UnidadNarrativa.objects.filter(obra=self.obra, tipo='episodio', padre=arco)
        self.assertEqual(episodios.count(), 4)
        self.assertEqual(sorted(episodios.values_list('nombre', flat=True)),
                          ['Episodio 1', 'Episodio 2', 'Episodio 3', 'Episodio 4'])

    def test_rango_abierto_sin_hasta_episodio_no_crea_nada(self):
        self.ruta = _escribir_yaml({
            'obra_external_id': {'source': 'jikan', 'external_id': 777},
            'nodos': [{'tipo': 'arco', 'nombre': 'Arco Final', 'orden_local': 1, 'vincular_episodios': [1156, None]}],
        })
        salida = StringIO()
        call_command('importar_estructura', self.ruta, stdout=salida)
        self.assertEqual(UnidadNarrativa.objects.filter(obra=self.obra, tipo='episodio').count(), 0)
        self.assertIn('rango abierto', salida.getvalue())

    def test_rango_abierto_con_hasta_episodio_lo_cierra(self):
        self.ruta = _escribir_yaml({
            'obra_external_id': {'source': 'jikan', 'external_id': 777},
            'nodos': [{'tipo': 'arco', 'nombre': 'Arco Final', 'orden_local': 1, 'vincular_episodios': [10, None]}],
        })
        call_command('importar_estructura', self.ruta, hasta_episodio=12, stdout=StringIO())
        self.assertEqual(UnidadNarrativa.objects.filter(obra=self.obra, tipo='episodio').count(), 3)


class ImportarEstructuraMangaTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo='Manga X', slug='manga-x', tipo=Obra.TIPO_MANGA)
        ExternalId.objects.create(source='jikan', external_id='888', obra=self.obra)
        self.ruta = None

    def tearDown(self):
        if self.ruta and os.path.exists(self.ruta):
            os.unlink(self.ruta)

    def test_crea_capitulos_desde_rango_cerrado(self):
        self.ruta = _escribir_yaml({
            'obra_external_id': {'source': 'jikan', 'external_id': 888},
            'nodos': [{'tipo': 'arco', 'nombre': 'Arco Piloto', 'orden_local': 1, 'vincular_capitulos': [1, 5]}],
        })
        call_command('importar_estructura', self.ruta, stdout=StringIO())
        self.assertEqual(UnidadNarrativa.objects.filter(obra=self.obra, tipo='capitulo').count(), 5)

    def test_rango_abierto_sin_hasta_capitulo_no_crea_nada(self):
        self.ruta = _escribir_yaml({
            'obra_external_id': {'source': 'jikan', 'external_id': 888},
            'nodos': [{'tipo': 'arco', 'nombre': 'Arco Abierto', 'orden_local': 1, 'vincular_capitulos': [1, None]}],
        })
        salida = StringIO()
        call_command('importar_estructura', self.ruta, stdout=salida)
        self.assertEqual(UnidadNarrativa.objects.filter(obra=self.obra, tipo='capitulo').count(), 0)
        self.assertIn('rango abierto', salida.getvalue())

    def test_rango_abierto_con_hasta_capitulo_lo_cierra(self):
        self.ruta = _escribir_yaml({
            'obra_external_id': {'source': 'jikan', 'external_id': 888},
            'nodos': [{'tipo': 'arco', 'nombre': 'Arco Abierto', 'orden_local': 1, 'vincular_capitulos': [10, None]}],
        })
        call_command('importar_estructura', self.ruta, hasta_capitulo=12, stdout=StringIO())
        self.assertEqual(UnidadNarrativa.objects.filter(obra=self.obra, tipo='capitulo').count(), 3)

    def test_temas_transversales_vincula_capitulos_por_rango(self):
        self.ruta = _escribir_yaml({
            'obra_external_id': {'source': 'jikan', 'external_id': 888},
            'nodos': [{'tipo': 'arco', 'nombre': 'Arco', 'orden_local': 1, 'vincular_capitulos': [1, 10]}],
            'temas_transversales': [
                {'nombre': 'Minihistoria X', 'tipo': 'minihistoria', 'rango_capitulos': [3, 5], 'revisar': True},
            ],
        })
        call_command('importar_estructura', self.ruta, stdout=StringIO())

        tema = TemaTransversal.objects.get(obra=self.obra, nombre='Minihistoria X')
        self.assertEqual(tema.tipo, TemaTransversal.TIPO_MINIHISTORIA)
        self.assertEqual(tema.unidades.count(), 3)


class ImportarEstructuraFechasVolumenTests(TestCase):
    """Aproximación de fecha de capítulo por reparto proporcional dentro
    del rango de volúmenes del arco (--fechas-volumen)."""

    def setUp(self):
        self.obra = Obra.objects.create(titulo='Manga Z', slug='manga-z', tipo=Obra.TIPO_MANGA)
        ExternalId.objects.create(source='jikan', external_id='555', obra=self.obra)
        self.ruta_estructura = None
        self.ruta_fechas = _escribir_yaml({1: '2000-01-01', 2: '2000-02-01', 3: '2000-03-01'})

    def tearDown(self):
        if self.ruta_estructura and os.path.exists(self.ruta_estructura):
            os.unlink(self.ruta_estructura)
        os.unlink(self.ruta_fechas)

    def test_reparte_capitulos_entre_volumenes_proporcionalmente(self):
        self.ruta_estructura = _escribir_yaml({
            'obra_external_id': {'source': 'jikan', 'external_id': 555},
            'nodos': [{
                'tipo': 'arco', 'nombre': 'Arco', 'orden_local': 1,
                'vincular_capitulos': [1, 9], 'volumenes': [1, 3],
            }],
        })
        call_command(
            'importar_estructura', self.ruta_estructura,
            fechas_volumen=self.ruta_fechas, stdout=StringIO(),
        )

        fechas = {
            u.orden_local: u.fecha
            for u in UnidadNarrativa.objects.filter(obra=self.obra, tipo='capitulo')
        }
        self.assertEqual([fechas[n] for n in (1, 2, 3)], [date(2000, 1, 1)] * 3)
        self.assertEqual([fechas[n] for n in (4, 5, 6)], [date(2000, 2, 1)] * 3)
        self.assertEqual([fechas[n] for n in (7, 8, 9)], [date(2000, 3, 1)] * 3)

    def test_volumen_unico_asigna_la_misma_fecha_a_todos(self):
        self.ruta_estructura = _escribir_yaml({
            'obra_external_id': {'source': 'jikan', 'external_id': 555},
            'nodos': [{
                'tipo': 'arco', 'nombre': 'Arco', 'orden_local': 1,
                'vincular_capitulos': [1, 5], 'volumenes': [2, 2],
            }],
        })
        call_command(
            'importar_estructura', self.ruta_estructura,
            fechas_volumen=self.ruta_fechas, stdout=StringIO(),
        )

        fechas = set(UnidadNarrativa.objects.filter(
            obra=self.obra, tipo='capitulo'
        ).values_list('fecha', flat=True))
        self.assertEqual(fechas, {date(2000, 2, 1)})

    def test_sin_fechas_volumen_no_asigna_fecha(self):
        self.ruta_estructura = _escribir_yaml({
            'obra_external_id': {'source': 'jikan', 'external_id': 555},
            'nodos': [{
                'tipo': 'arco', 'nombre': 'Arco', 'orden_local': 1,
                'vincular_capitulos': [1, 3], 'volumenes': [1, 1],
            }],
        })
        call_command('importar_estructura', self.ruta_estructura, stdout=StringIO())

        fechas = set(UnidadNarrativa.objects.filter(
            obra=self.obra, tipo='capitulo'
        ).values_list('fecha', flat=True))
        self.assertEqual(fechas, {None})


class JikanClientPaginacionTests(TestCase):
    """Regresión del bug real encontrado durante la importación de One
    Piece: cuando Jikan no da el total de episodios (obra en emisión) y
    una página falla, el recorrido NO debe abortar — debe seguir hasta
    encontrar una página que confirme que no hay más, o hasta el límite
    de seguridad. La versión original se paraba en la primera página
    fallida precisamente en este caso (total desconocido)."""

    @staticmethod
    def _respuesta(status_code, body):
        resp = Mock()
        resp.status_code = status_code
        resp.json.return_value = body
        resp.text = str(body)
        return resp

    @patch('narrative.services.jikan_client.time.sleep')
    @patch('narrative.services.jikan_client.requests.get')
    def test_sigue_tras_pagina_fallida_cuando_total_es_desconocido(self, mock_get, mock_sleep):
        pagina_1_falla = self._respuesta(500, {'status': 500})
        pagina_2_ok_sin_siguiente = self._respuesta(200, {
            'data': [{'mal_id': 1, 'title': 'Ep 1'}],
            'pagination': {'has_next_page': False},
        })
        # intentos=2 por página de episodios: la 1 agota sus 2 intentos, luego pasa a la 2.
        mock_get.side_effect = [pagina_1_falla, pagina_1_falla, pagina_2_ok_sin_siguiente]

        episodios, fallidas = jikan_client.get_anime_episodes(21, total_episodios=None)

        self.assertEqual(fallidas, [1])
        self.assertEqual(len(episodios), 1)

    @patch('narrative.services.jikan_client.time.sleep')
    @patch('narrative.services.jikan_client.requests.get')
    def test_se_detiene_al_confirmar_que_no_hay_mas_paginas(self, mock_get, mock_sleep):
        mock_get.return_value = self._respuesta(200, {
            'data': [{'mal_id': 1, 'title': 'Ep 1'}],
            'pagination': {'has_next_page': False},
        })

        episodios, fallidas = jikan_client.get_anime_episodes(21, total_episodios=None)

        self.assertEqual(fallidas, [])
        self.assertEqual(mock_get.call_count, 1)

    @patch('narrative.services.jikan_client.time.sleep')
    @patch('narrative.services.jikan_client.requests.get')
    def test_con_total_conocido_para_en_el_numero_de_pagina_exacto(self, mock_get, mock_sleep):
        pagina = self._respuesta(200, {
            'data': [{'mal_id': i, 'title': f'Ep {i}'} for i in range(1, 101)],
            'pagination': {'has_next_page': True},
        })
        mock_get.return_value = pagina

        episodios, fallidas = jikan_client.get_anime_episodes(21, total_episodios=150)

        self.assertEqual(fallidas, [])
        self.assertEqual(mock_get.call_count, 2)  # ceil(150/100) = 2 páginas