"""Vídeos de YouTube en posts (v1, provisional: el objetivo es alojar vídeos propios sin nada ajeno al vídeo).
Solo se guarda el identificador; título y canal salen del oEmbed público de YouTube y se usan
también como contexto para la IA de fronteras. La portada se guarda como imagen propia."""

import json
import re
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlencode, urlparse

from django.core.exceptions import ValidationError

from core.imagenes.remotas import descargar_imagen

HOSTS_YOUTUBE = {
    'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be',
    'youtube-nocookie.com', 'www.youtube-nocookie.com',
}
PATRON_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
# Rutas con el identificador en el segundo segmento (/embed/ID, /shorts/ID...).
RUTAS_CON_ID = {'embed', 'shorts', 'live', 'v'}
URL_OEMBED = 'https://www.youtube.com/oembed'
TIMEOUT_S = 6
MAX_BYTES_OEMBED = 64 * 1024
# De mejor a peor calidad: maxresdefault no existe en todos los vídeos.
PORTADAS = ('maxresdefault', 'hqdefault')


class VideoNoValido(Exception):
    pass


def extraer_id_youtube(url):
    partes = urlparse((url or '').strip())
    host = (partes.hostname or '').lower()
    if partes.scheme not in ('http', 'https') or host not in HOSTS_YOUTUBE:
        raise VideoNoValido('Solo se admiten enlaces de YouTube.')
    if host == 'youtu.be':
        candidato = partes.path.lstrip('/').split('/')[0]
    elif partes.path == '/watch':
        candidato = parse_qs(partes.query).get('v', [''])[0]
    else:
        segmentos = [s for s in partes.path.split('/') if s]
        candidato = segmentos[1] if len(segmentos) >= 2 and segmentos[0] in RUTAS_CON_ID else ''
    if not PATRON_ID.match(candidato):
        raise VideoNoValido('No se reconoce el vídeo en ese enlace de YouTube.')
    return candidato


def consultar_oembed(video_id):
    """Título y canal. Falla si el vídeo no existe o su autor no permite insertarlo en otras webs."""
    consulta = urlencode({'url': f'https://www.youtube.com/watch?v={video_id}', 'format': 'json'})
    peticion = urllib.request.Request(f'{URL_OEMBED}?{consulta}', headers={'User-Agent': 'RevealLess/1.0'})
    try:
        with urllib.request.urlopen(peticion, timeout=TIMEOUT_S) as respuesta:
            datos = json.loads(respuesta.read(MAX_BYTES_OEMBED))
    except urllib.error.HTTPError as e:
        raise VideoNoValido('Ese vídeo no existe o su autor no permite insertarlo en otras webs.') from e
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        raise VideoNoValido('No se pudo comprobar el vídeo. Inténtalo de nuevo en un momento.') from e
    return {
        'titulo': str(datos.get('title') or '')[:200],
        'canal': str(datos.get('author_name') or '')[:150],
    }


def descargar_portada(video_id):
    """Miniatura guardada como imagen propia: antes de pulsar «play» no se pide nada a YouTube."""
    for calidad in PORTADAS:
        try:
            archivo = descargar_imagen(f'https://i.ytimg.com/vi/{video_id}/{calidad}.jpg')
        except ValidationError:
            continue
        archivo.name = f'{video_id}.jpg'
        return archivo
    return None


def resolver_video(url):
    video_id = extraer_id_youtube(url)
    return {'id': video_id, **consultar_oembed(video_id)}


def texto_con_video(texto, titulo='', canal=''):
    """Texto para la IA: el título del vídeo puede revelar lo que el post no dice."""
    if not titulo:
        return texto
    origen = f' (canal: {canal})' if canal else ''
    return f'{texto}\n\n[Vídeo adjunto: «{titulo}»{origen}]'


def aplicar_video(post, video):
    post.video_youtube_id = video['id']
    post.video_titulo = video['titulo']
    post.video_canal = video['canal']
    post.video_portada = descargar_portada(video['id'])


def quitar_video(post):
    post.video_youtube_id = ''
    post.video_titulo = ''
    post.video_canal = ''
    post.video_portada = None