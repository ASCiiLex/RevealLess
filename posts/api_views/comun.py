from rest_framework import status
from rest_framework.response import Response

from narrative.models import UnidadNarrativa

ERROR_CRUZADA_INCOMPLETA = 'Indica la obra cruzada y su frontera juntas, o ninguna de las dos.'
ERROR_CRUZADA_SIN_FRONTERA = {
    'frontera_cruzada': ['Indica de qué parte de la obra comparada hablas o enfrenta a algún personaje suyo.'],
}
ERROR_TEMA_OTRA_OBRA = {'tema': ['Debe pertenecer a la obra del post.']}
ERROR_SIN_REFERENCIA = {'referencia_narrativa': ['Indica de qué parte o tema habla el post, o su frontera de spoiler.']}
ERROR_IMAGEN_Y_GALERIA = {'imagenes': ['Envía una imagen o una galería, no ambas.']}
ERROR_DISPOSICION = {'disposicion': ['Esa disposición no es válida para ese número de imágenes.']}
ERROR_NUMERO_COMPARADOS = {'personajes_comparados': ['Una comparativa necesita de 2 a 4 personajes.']}
ERROR_COMPARADO_AJENO = {'personajes_comparados': ['Cada personaje debe pertenecer a la obra o a la obra comparada.']}
ERROR_MODO_CRUCE = {'modo_cruce': ['La misma escena solo vale entre adaptaciones de una misma historia.']}


def error_400(detail):
    return Response({'detail': detail}, status=status.HTTP_400_BAD_REQUEST)


def tema_de_otra_obra(tema, obra_id):
    return bool(tema) and tema.obra_id != obra_id


def frontera_minima(frontera, referencia):
    """La parte es contexto, pero el contexto también informa: la frontera nunca queda por
    debajo del primer episodio de la parte de la que habla el post (un previo, justo antes)."""
    if not (frontera and referencia):
        return frontera
    primera_hoja = UnidadNarrativa.objects.filter(
        obra_id=referencia.obra_id, orden_inicio=referencia.orden_inicio, hijos__isnull=True,
    ).first()
    if primera_hoja and frontera.orden_frontera < primera_hoja.orden_frontera:
        return primera_hoja
    return frontera