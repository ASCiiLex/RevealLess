from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from ..models import Obra, UnidadNarrativa, ExternalId
from ..services import jikan_client

JIKAN = 'narrative.services.jikan_client'

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


def _importar(tipo, external_id):
    call_command('importar_catalogo', tipo=tipo, external_id=external_id, stdout=StringIO())


@patch(f'{JIKAN}.get_relations', return_value=[])
@patch(f'{JIKAN}.get_anime_episodes', return_value=([], []))
@patch(f'{JIKAN}.get_anime', return_value=ANIME_DATA)
class ImportarCatalogoAnimeTests(TestCase):
    # Orden de mocks en la firma: de abajo arriba respecto a los decoradores.

    def test_crea_obra_y_episodios(self, mock_anime, mock_episodios, mock_relations):
        mock_episodios.return_value = (
            [
                {'mal_id': 1, 'title': 'Romance Dawn', 'aired': '1999-10-20'},
                {'mal_id': 2, 'title': 'That Girl', 'aired': '1999-10-27'},
                {'mal_id': 3, 'title': 'Morgan', 'aired': '1999-11-03'},
            ],
            [],
        )
        _importar('anime', 21)

        obra = Obra.objects.get(tipo=Obra.TIPO_SERIE)
        self.assertEqual(obra.titulo, 'One Piece')
        self.assertEqual(obra.autor, 'Estudio: Toei Animation')
        self.assertTrue(ExternalId.objects.filter(source='jikan', external_id='21', obra=obra).exists())

        self.assertEqual(UnidadNarrativa.objects.filter(obra=obra, tipo='episodio').count(), 3)
        for ep_id in (1, 2, 3):
            self.assertTrue(ExternalId.objects.filter(source='jikan', external_id=str(ep_id)).exists())

    def test_idempotente_no_duplica_obra_ni_externalid(self, mock_anime, mock_episodios, mock_relations):
        _importar('anime', 21)
        _importar('anime', 21)

        self.assertEqual(Obra.objects.filter(tipo=Obra.TIPO_SERIE).count(), 1)
        self.assertEqual(ExternalId.objects.filter(source='jikan', external_id='21').count(), 1)

    def test_mapea_tipo_jikan_movie_a_pelicula(self, mock_anime, mock_episodios, mock_relations):
        mock_anime.return_value = {**ANIME_DATA, 'type': 'Movie', 'title': 'One Piece: La Película'}
        _importar('anime', 1)

        obra = Obra.objects.get(tipo=Obra.TIPO_PELICULA)
        self.assertEqual(obra.titulo, 'One Piece: La Película')

    def test_evita_colision_de_slug_con_manga_del_mismo_titulo(self, mock_anime, mock_episodios, mock_relations):
        _importar('anime', 21)
        with patch(f'{JIKAN}.get_manga', return_value=MANGA_DATA):
            _importar('manga', 13)

        slugs = set(Obra.objects.values_list('slug', flat=True))
        self.assertEqual(len(slugs), 2)

    def test_adopta_placeholder_creado_por_fase_b_en_vez_de_duplicar(self, mock_anime, mock_episodios, mock_relations):
        obra = Obra.objects.create(titulo='One Piece', slug='one-piece', tipo=Obra.TIPO_SERIE)
        ExternalId.objects.create(source='jikan', external_id='21', obra=obra)
        arco = UnidadNarrativa.objects.create(
            obra=obra, tipo='arco', nombre='Arco de Romance Dawn', orden_local=1,
        )
        placeholder = UnidadNarrativa.objects.create(
            obra=obra, padre=arco, tipo='episodio', nombre='Episodio 1', orden_local=1,
        )

        mock_episodios.return_value = (
            [{'mal_id': 1, 'title': 'Romance Dawn', 'aired': '1999-10-20'}],
            [],
        )
        _importar('anime', 21)

        # Misma fila (mismo pk), con datos reales y conservando el padre.
        self.assertEqual(UnidadNarrativa.objects.filter(obra=obra, tipo='episodio').count(), 1)
        placeholder.refresh_from_db()
        self.assertEqual(placeholder.nombre, 'Romance Dawn')
        self.assertEqual(placeholder.padre_id, arco.id)
        self.assertTrue(ExternalId.objects.filter(source='jikan', external_id='1', unidad=placeholder).exists())


class ImportarCatalogoMangaTests(TestCase):
    @patch(f'{JIKAN}.get_relations', return_value=[])
    @patch(f'{JIKAN}.get_manga', return_value=MANGA_DATA)
    def test_crea_obra_sin_episodios_ni_capitulos(self, mock_manga, mock_relations):
        _importar('manga', 13)

        obra = Obra.objects.get(tipo=Obra.TIPO_MANGA)
        self.assertEqual(obra.autor, 'Eiichiro Oda')
        self.assertEqual(UnidadNarrativa.objects.filter(obra=obra).count(), 0)

    @patch(f'{JIKAN}.get_relations', side_effect=jikan_client.JikanError('504 simulado'))
    @patch(f'{JIKAN}.get_manga', return_value=MANGA_DATA)
    def test_fallo_en_relations_no_aborta_el_comando(self, mock_manga, mock_relations):
        """Regresión: un fallo en relations no pierde la Obra ya creada."""
        _importar('manga', 13)
        self.assertTrue(Obra.objects.filter(tipo=Obra.TIPO_MANGA).exists())


class CrearObraManualTests(TestCase):
    def test_crea_obra_con_externalid_manual(self):
        call_command(
            'crear_obra_manual', slug='star-wars', titulo='Star Wars',
            tipo=Obra.TIPO_SERIE, stdout=StringIO(),
        )
        obra = Obra.objects.get(slug='star-wars')
        self.assertTrue(
            ExternalId.objects.filter(source=ExternalId.SOURCE_MANUAL, external_id='star-wars', obra=obra).exists()
        )

    def test_es_idempotente(self):
        for _ in range(2):
            call_command('crear_obra_manual', slug='star-wars', titulo='Star Wars', stdout=StringIO())
        self.assertEqual(Obra.objects.filter(slug='star-wars').count(), 1)
        self.assertEqual(
            ExternalId.objects.filter(source=ExternalId.SOURCE_MANUAL, external_id='star-wars').count(), 1,
        )