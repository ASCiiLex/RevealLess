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
# 'mul': etiqueta común a todos los idiomas, cada vez más usada en Wikidata.
IDIOMAS = 'es,mul,en'
PRECISION_DIA = 11

CLASE_PELICULA = 'pelicula'
CLASE_TV = 'tv'
CLASE_OTRA = 'otra'


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
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{IDIOMAS}". }}
        }}''')
    return [{'qid': _qid(f['p']['value']), 'nombre': f['pLabel']['value']} for f in filas]


def _clases_de_partes(qid):
    """{item: clase}. Consulta aparte: combinar las subclases con fechas y personajes
    multiplica las filas y acerca la consulta principal al límite de tiempo."""
    filas = _sparql(f'''
        SELECT ?item ?esPelicula ?esTv WHERE {{
          ?item (wdt:P179|wdt:P361)+ wd:{qid} .
          BIND(EXISTS {{ ?item wdt:P31/wdt:P279* wd:Q11424 }} AS ?esPelicula)
          BIND(EXISTS {{
            VALUES ?tv {{ wd:Q21191270 wd:Q5398426 wd:Q3464665 }}
            ?item wdt:P31/wdt:P279* ?tv
          }} AS ?esTv)
        }}''')
    clases = {}
    for f in filas:
        if f['esTv']['value'] == 'true':
            clases[_qid(f['item']['value'])] = CLASE_TV
        elif f['esPelicula']['value'] == 'true':
            clases[_qid(f['item']['value'])] = CLASE_PELICULA
    return clases


def partes_de_obra(qid):
    """Elementos que forman parte de la obra, a cualquier profundidad (P179 serie o
    P361 parte de): películas bajo sus fases, episodios bajo sus temporadas...
    'fechas': todas las de precisión de día (premieres, estrenos por país); quien
    empareja elige la más cercana. [{qid, titulo, fechas, clase, personajes}]"""
    filas = _sparql(f'''
        SELECT ?item ?itemLabel ?fecha ?precision ?p ?pLabel WHERE {{
          ?item (wdt:P179|wdt:P361)+ wd:{qid} .
          OPTIONAL {{
            ?item p:P577/psv:P577 ?valor .
            ?valor wikibase:timeValue ?fecha ; wikibase:timePrecision ?precision .
          }}
          OPTIONAL {{ ?item wdt:P674 ?p }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{IDIOMAS}". }}
        }}''')
    clases = _clases_de_partes(qid)

    partes = {}
    for f in filas:
        item = _qid(f['item']['value'])
        parte = partes.setdefault(item, {
            'qid': item, 'titulo': f['itemLabel']['value'], 'fechas': set(),
            'clase': clases.get(item, CLASE_OTRA), 'personajes': {},
        })
        if 'fecha' in f and int(f.get('precision', {}).get('value', 0)) >= PRECISION_DIA:
            fecha = _fecha(f['fecha']['value'])
            if fecha:
                parte['fechas'].add(fecha)
        if 'p' in f:
            parte['personajes'][_qid(f['p']['value'])] = f['pLabel']['value']

    return [
        {
            **p,
            'fechas': sorted(p['fechas']),
            'personajes': [{'qid': q, 'nombre': n} for q, n in p['personajes'].items()],
        }
        for p in partes.values()
    ]