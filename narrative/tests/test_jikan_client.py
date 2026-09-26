from unittest.mock import patch, Mock

from django.test import TestCase

from ..services import jikan_client

JIKAN = 'narrative.services.jikan_client'


def _respuesta(status_code, body):
    resp = Mock()
    resp.status_code = status_code
    resp.json.return_value = body
    resp.text = str(body)
    return resp


@patch(f'{JIKAN}.time.sleep')
@patch(f'{JIKAN}.requests.get')
class JikanClientPaginacionTests(TestCase):
    """Regresión One Piece: con total desconocido, una página fallida no
    debe abortar el recorrido; se sigue hasta confirmar que no hay más."""

    def test_sigue_tras_pagina_fallida_cuando_total_es_desconocido(self, mock_get, mock_sleep):
        pagina_1_falla = _respuesta(500, {'status': 500})
        pagina_2_ok = _respuesta(200, {
            'data': [{'mal_id': 1, 'title': 'Ep 1'}],
            'pagination': {'has_next_page': False},
        })
        # 2 intentos por página: la 1 los agota y pasa a la 2.
        mock_get.side_effect = [pagina_1_falla, pagina_1_falla, pagina_2_ok]

        episodios, fallidas = jikan_client.get_anime_episodes(21, total_episodios=None)

        self.assertEqual(fallidas, [1])
        self.assertEqual(len(episodios), 1)

    def test_se_detiene_al_confirmar_que_no_hay_mas_paginas(self, mock_get, mock_sleep):
        mock_get.return_value = _respuesta(200, {
            'data': [{'mal_id': 1, 'title': 'Ep 1'}],
            'pagination': {'has_next_page': False},
        })

        _, fallidas = jikan_client.get_anime_episodes(21, total_episodios=None)

        self.assertEqual(fallidas, [])
        self.assertEqual(mock_get.call_count, 1)

    def test_con_total_conocido_para_en_el_numero_de_pagina_exacto(self, mock_get, mock_sleep):
        mock_get.return_value = _respuesta(200, {
            'data': [{'mal_id': i, 'title': f'Ep {i}'} for i in range(1, 101)],
            'pagination': {'has_next_page': True},
        })

        _, fallidas = jikan_client.get_anime_episodes(21, total_episodios=150)

        self.assertEqual(fallidas, [])
        self.assertEqual(mock_get.call_count, 2)