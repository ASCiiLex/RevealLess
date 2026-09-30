"""Cliente mínimo de Wikidata (CC0): búsqueda de entidades y consultas SPARQL."""

import time
from datetime import date

import requests

API_URL = 'https://www.wikidata.org/w/api.php'
SPARQL_URL = 'https://query.wikidata.org/sparql'
# Wikidata exige un User-Agent identificable.
USER_AGENT = 'RevealLess/1.0 (TFM Master Full Stack; importador de personajes)'
TIMEOUT = 60
INTENTOS = 3
REINTENTABLES = {429, 500, 502, 503, 504}


class WikidataError(Exception):
    pass


def _get(url, params):
    ultimo_error = 'sin detalle'
    for intento in range(1, INTENTOS + 1):
        try:
            resp = requests.get(
                url, params=params, timeout=TIMEOUT,
                headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'},
            )
        except requests.RequestException as exc:
            ultimo_error = f'error de red: {exc}'
        else:
            if resp.status_code == 200:
                return resp.json()
            ultimo_error = f'{resp.status_code}: {resp.text[:200]}'
            if resp.status_code not in REINTENTABLES:
                break
        time.sleep(2 * intento)
    raise WikidataError(f'Fallo en {url} — {ultimo_error}')


def _qid(uri):
    return uri.rsplit('/', 1)[-1]


def _fecha(valor):
    try:
        return date.fromisoformat(valor[:10])
    except ValueError:
        return None


def _sparql(consulta):
    return _get(SPARQL_URL, {'query': consulta, 'format': 'json'})['results']['bindings']


def buscar_entidades(texto, idioma='es', limite=5):
    data = _get(API_URL, {
        'action': 'wbsearchentities', 'search': texto, 'language': idioma, 'uselang': idioma,
        'type': 'item', 'limit': limite, 'format': 'json',
    })
    return [
        {'id': r['id'], 'label': r.get('label', ''), 'descripcion': r.get('description', '')}
        for r in data.get('search', [])
    ]


def personajes_de_obra(qid):
    """[{qid, nombre}] de la propiedad P674 (personajes) de la obra."""
    filas = _sparql(f'''
        SELECT ?p ?pLabel WHERE {{
          wd:{qid} wdt:P674 ?p .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
        }}''')
    return [{'qid': _qid(f['p']['value']), 'nombre': f['pLabel']['value']} for f in filas]


def partes_de_obra(qid):
    """Elementos que forman parte de la obra (P179 serie o P361 parte de): películas,
    temporadas, episodios. [{qid, titulo, fecha, personajes: [{qid, nombre}]}]"""
    filas = _sparql(f'''
        SELECT ?item ?itemLabel ?fecha ?p ?pLabel WHERE {{
          {{ ?item wdt:P179 wd:{qid} }} UNION {{ ?item wdt:P361 wd:{qid} }}
          OPTIONAL {{ ?item wdt:P577 ?fecha }}
          OPTIONAL {{ ?item wdt:P674 ?p }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
        }}''')

    partes = {}
    for f in filas:
        item = _qid(f['item']['value'])
        parte = partes.setdefault(item, {
            'qid': item, 'titulo': f['itemLabel']['value'], 'fecha': None, 'personajes': {},
        })
        if 'fecha' in f:
            fecha = _fecha(f['fecha']['value'])
            # Varias fechas de estreno (por país): vale la primera.
            if fecha and (parte['fecha'] is None or fecha < parte['fecha']):
                parte['fecha'] = fecha
        if 'p' in f:
            parte['personajes'][_qid(f['p']['value'])] = f['pLabel']['value']

    return [
        {**p, 'personajes': [{'qid': q, 'nombre': n} for q, n in p['personajes'].items()]}
        for p in partes.values()
    ]