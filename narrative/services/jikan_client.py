import time
import requests

BASE_URL = 'https://api.jikan.moe/v4'
# Límite documentado: 3 req/s, 60 req/min. Margen conservador.
DELAY_ENTRE_LLAMADAS = 0.45
INTENTOS_POR_DEFECTO = 4
ERRORES_TRANSITORIOS = {500, 502, 503, 504}
EPISODIOS_POR_PAGINA = 100


class JikanError(Exception):
    pass


def _get(path, params=None, intentos=INTENTOS_POR_DEFECTO):
    """Toda llamada a Jikan pasa por aquí — por eso el progreso se
    imprime en un solo sitio. Sin esto, un fallo transitorio con
    reintento (backoff hasta 8s por intento, hasta 4 intentos) es
    indistinguible de un cuelgue: no hay NINGÚN output hasta que se
    agotan los reintentos o responde con éxito."""
    url = f'{BASE_URL}{path}'
    ultimo_error = 'sin detalle'
    multiples = intentos > 1

    for intento in range(1, intentos + 1):
        if multiples:
            print(f'  jikan: {path} (intento {intento}/{intentos})...', end=' ', flush=True)
        time.sleep(DELAY_ENTRE_LLAMADAS)
        try:
            resp = requests.get(url, params=params, timeout=15)
        except requests.RequestException as exc:
            ultimo_error = f'error de red: {exc}'
            if multiples:
                print(f'FALLO ({ultimo_error})')
            continue

        if resp.status_code == 429:
            ultimo_error = '429 rate limit'
            if multiples:
                print(f'{ultimo_error}, esperando 2s...')
            time.sleep(2)
            continue

        if resp.status_code in ERRORES_TRANSITORIOS:
            ultimo_error = f'{resp.status_code}: {resp.text[:200]}'
            espera = 2 * intento  # backoff creciente
            if multiples:
                print(f'FALLO ({ultimo_error}), esperando {espera}s...')
            time.sleep(espera)
            continue

        if resp.status_code != 200:
            # Error no transitorio (404, 400...) — no tiene sentido reintentar.
            if multiples:
                print('FALLO (no reintentable)')
            raise JikanError(f'{resp.status_code} en {url}: {resp.text[:200]}')

        body = resp.json()
        if 'data' not in body:
            # 200 con cuerpo inesperado (a veces Jikan lo devuelve así en
            # sus propias caídas) — se trata igual que un fallo transitorio.
            ultimo_error = f'respuesta 200 sin "data": {str(body)[:200]}'
            espera = 2 * intento
            if multiples:
                print(f'FALLO ({ultimo_error}), esperando {espera}s...')
            time.sleep(espera)
            continue

        if multiples:
            print('ok')
        return body

    raise JikanError(f'Fallo tras {intentos} intentos en {url} — último error: {ultimo_error}')


def get_anime(mal_id):
    return _get(f'/anime/{mal_id}')['data']


def get_manga(mal_id):
    return _get(f'/manga/{mal_id}')['data']


MAX_PAGINAS_SIN_TOTAL_CONOCIDO = 20  # 2000 episodios de margen si Jikan no da el total (obra en emisión)


def get_anime_episodes(mal_id, total_episodios=None, max_paginas=MAX_PAGINAS_SIN_TOTAL_CONOCIDO):
    """Devuelve (episodios, paginas_fallidas) — NO es un generador que
    aborta en el primer fallo. Cada página se reintenta un par de veces
    (menos que el resto de llamadas: aquí puede haber hasta 20 páginas,
    así que agotar 4 intentos por página antes de pasar a la siguiente
    dispara el tiempo total sin aportar fiabilidad extra — el comando ya
    es relanzable para rellenar lo que falte).

    total_episodios (del propio detalle de la obra, ya conocido antes de
    llamar aquí) permite calcular cuántas páginas hay exactas. Si es None
    (obra en emisión: Jikan no conoce el total todavía), se recorre hasta
    max_paginas SIN detenerse por que una página falle — solo se para de
    verdad cuando una página que sí responde confirma que no hay
    siguiente. Detenerse en el primer fallo cuando el total es
    desconocido perdería toda la importación por una sola página lenta.

    Imprime progreso por página (print, no logging: es una herramienta
    de consola de un solo uso, no una vista de producción) porque sin
    esto el comando es indistinguible de un cuelgue durante minutos."""
    episodios = []
    paginas_fallidas = []
    total_paginas = max(1, -(-total_episodios // EPISODIOS_POR_PAGINA)) if total_episodios else None
    limite = total_paginas or max_paginas

    page = 1
    while page <= limite:
        print(f'  episodios: página {page}/{limite}...', end=' ', flush=True)
        try:
            data = _get(f'/anime/{mal_id}/episodes', params={'page': page}, intentos=2)
        except JikanError as exc:
            paginas_fallidas.append(page)
            print(f'FALLO ({exc})')
            page += 1
            continue

        episodios.extend(data['data'])
        print(f'ok ({len(data["data"])} episodios)')

        if total_paginas is not None:
            if page >= total_paginas:
                break
        elif not data.get('pagination', {}).get('has_next_page'):
            break
        page += 1

    return episodios, paginas_fallidas


def get_relations(mal_id, tipo):
    """tipo: 'anime' o 'manga'. Devuelve la lista de relations tal cual
    la da Jikan: [{relation: 'Adaptation'|'Sequel'|..., entry: [{mal_id,
    type, name, url}, ...]}, ...]"""
    return _get(f'/{tipo}/{mal_id}/relations')['data']


def get_characters(mal_id, tipo):
    """tipo: 'anime' o 'manga'. [{mal_id, nombre, rol}] con rol 'Main' o 'Supporting'.
    Nombres en formato MAL: 'Apellido, Nombre'."""
    datos = _get(f'/{tipo}/{mal_id}/characters')['data']
    return [
        {'mal_id': d['character']['mal_id'], 'nombre': d['character']['name'], 'rol': d.get('role', '')}
        for d in datos
    ]


def search(query, tipo):
    """tipo: 'anime' o 'manga'. Devuelve la lista de resultados de
    búsqueda tal cual los da Jikan (para uso interactivo, no en el
    comando de importación que exige --external-id explícito)."""
    return _get(f'/{tipo}', params={'q': query, 'limit': 10})['data']