from rest_framework import status
from rest_framework.response import Response

from narrative.services.fronteras import (
    frontera_minima,
    frontera_minima_temas,
    frontera_sin_previa_cerrada,
    previa_cerrada,
)

ERROR_CRUZADA_INCOMPLETA = 'Indica la obra cruzada y su frontera juntas, o ninguna de las dos.'
ERROR_CRUZADA_SIN_FRONTERA = {
    'frontera_cruzada': ['Indica de qué parte de la obra comparada hablas o enfrenta a algún personaje suyo.'],
}
MENSAJE_PREVIA_CERRADA = 'Ese previo al estreno ya está cerrado: elige como frontera una parte ya estrenada.'
ERROR_PREVIA_CERRADA = {'frontera_spoiler': [MENSAJE_PREVIA_CERRADA]}
ERROR_PREVIA_CERRADA_CRUZADA = {'frontera_cruzada': [MENSAJE_PREVIA_CERRADA]}
ERROR_TEMA_OTRA_OBRA = {'tema': ['Debe pertenecer a la obra del post.']}
ERROR_SIN_REFERENCIA = {'referencia_narrativa': ['Indica de qué parte o tema habla el post, o su frontera de spoiler.']}
ERROR_IMAGEN_Y_GALERIA = {'imagenes': ['Envía una imagen o una galería, no ambas.']}
ERROR_VIDEO_E_IMAGENES = {'video_url': ['Un post lleva vídeo o imágenes, no ambas cosas.']}
ERROR_DISPOSICION = {'disposicion': ['Esa disposición no es válida para ese número de imágenes.']}
ERROR_NUMERO_COMPARADOS = {'personajes_comparados': ['Una comparativa necesita de 2 a 4 personajes.']}
ERROR_COMPARADO_AJENO = {'personajes_comparados': ['Cada personaje debe pertenecer a la obra o a la obra comparada.']}
ERROR_MODO_CRUCE = {'modo_cruce': ['La misma escena solo vale entre adaptaciones de una misma historia.']}

__all__ = [
    'error_400', 'error_video', 'frontera_minima', 'frontera_minima_temas', 'frontera_sin_previa_cerrada',
    'previa_cerrada', 'tema_de_otra_obra',
]


def error_400(detail):
    return Response({'detail': detail}, status=status.HTTP_400_BAD_REQUEST)


def error_video(exc):
    return error_400({'video_url': [str(exc)]})


def tema_de_otra_obra(tema, obra_id):
    return bool(tema) and tema.obra_id != obra_id