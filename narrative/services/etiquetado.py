"""Etiquetado automático de personajes en posts a partir del texto.
Solo candidatos ya aparecidos hasta la frontera del post: quien puede leer
el post ya los conoce, así que la etiqueta nunca adelanta nada."""

import re
import unicodedata
from collections import defaultdict

from ..models import Personaje

LONGITUD_MINIMA_PALABRA = 4
# Tratamientos y títulos: no identifican a nadie por sí solos.
PALABRAS_GENERICAS = {
    'capitan', 'maestre', 'senor', 'senora', 'doctor', 'doctora', 'principe', 'princesa',
    'reina', 'lord', 'lady', 'general', 'almirante', 'comandante', 'emperador', 'emperatriz',
}
# Nombres que también son palabras corrientes («sólo» no es Han Solo): exigen mayúscula inicial.
# Al inicio de frase pueden dar un falso positivo; riesgo aceptado, la etiqueta no cambia la visibilidad.
PALABRAS_COMUNES = {
    'solo', 'rey', 'gran', 'luz', 'sol', 'luna', 'mar', 'ley', 'fuerza', 'fuego', 'hielo',
    'sombra', 'muerte', 'vida', 'rojo', 'negro', 'blanco', 'gris', 'verde', 'joven', 'viejo',
    'santo', 'dios', 'diablo', 'hombre', 'mujer', 'nino', 'nina',
}


def _normalizar(texto):
    descompuesto = unicodedata.normalize('NFKD', texto)
    return ''.join(c for c in descompuesto if not unicodedata.combining(c)).lower()


def _contiene(texto_norm, termino_norm):
    return re.search(rf'(?<!\w){re.escape(termino_norm)}(?!\w)', texto_norm) is not None


def _palabras(texto):
    """Palabras normalizadas del texto, y las que aparecen con mayúscula inicial en el original."""
    todas, con_mayuscula = set(), set()
    for palabra in re.findall(r'\w+', texto):
        normalizada = _normalizar(palabra)
        todas.add(normalizada)
        if palabra[0].isupper():
            con_mayuscula.add(normalizada)
    return todas, con_mayuscula


def _nombrado(termino, texto_norm, palabras):
    """Varias palabras: búsqueda flexible. Una sola: palabra exacta, y con mayúscula si es corriente."""
    if not re.fullmatch(r'\w+', termino):
        return _contiene(texto_norm, termino)
    todas, con_mayuscula = palabras
    if termino in PALABRAS_COMUNES:
        return termino in con_mayuscula
    return termino in todas


def _terminos_por_personaje(obra_id, hasta_orden):
    candidatos = (
        Personaje.objects.filter(unidades__obra_id=obra_id, unidades__orden_fin__lte=hasta_orden)
        .distinct()
        .prefetch_related('etapas__visible_tras')
    )
    terminos = {}
    for p in candidatos:
        nombres = {p.nombre} | {
            e.alias for e in p.etapas.all()
            if e.alias and e.visible_tras.obra_id == obra_id and e.visible_tras.orden_fin <= hasta_orden
        }
        terminos[p.id] = {_normalizar(n) for n in nombres}
    return terminos


def personajes_mencionados(texto, obra_id, hasta_orden):
    """Ids de personajes de la obra, aparecidos hasta hasta_orden, nombrados en el texto.
    Coincide el nombre completo, un alias ya revelado o una palabra suelta del nombre
    que solo pertenezca a un candidato («Zoro» → Roronoa Zoro; «Monkey» no, es ambiguo)."""
    if not texto or hasta_orden is None:
        return set()

    terminos = _terminos_por_personaje(obra_id, hasta_orden)
    texto_norm = _normalizar(texto)
    palabras = _palabras(texto)
    encontrados = {
        pid for pid, ts in terminos.items() if any(_nombrado(t, texto_norm, palabras) for t in ts)
    }

    duenos = defaultdict(set)
    for pid, ts in terminos.items():
        for termino in ts:
            for palabra in re.findall(r'\w+', termino):
                if len(palabra) >= LONGITUD_MINIMA_PALABRA and palabra not in PALABRAS_GENERICAS:
                    duenos[palabra].add(pid)
    for palabra, pids in duenos.items():
        if len(pids) == 1 and _nombrado(palabra, texto_norm, palabras):
            encontrados |= pids

    return encontrados


def personajes_en_post(post):
    ids = personajes_mencionados(post.text, post.obra_id, post.frontera_orden)
    if post.obra_cruzada_id:
        ids |= personajes_mencionados(post.text, post.obra_cruzada_id, post.frontera_cruzada_orden)
    # Los de una comparativa cuentan siempre; los propuestos se añaden al aprobarlos.
    ids |= set(
        post.comparaciones.filter(personaje__isnull=False).values_list('personaje_id', flat=True)
    )
    return ids


def etiquetar_personajes(post):
    """Sustituye las etiquetas de personaje del post (ya guardado) por las detectadas."""
    ids = personajes_en_post(post)
    post.personajes.set(ids)
    return ids