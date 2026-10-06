from rest_framework import status
from rest_framework.response import Response

ERROR_CRUZADA_INCOMPLETA = 'Indica la obra cruzada y su frontera juntas, o ninguna de las dos.'
ERROR_TEMA_OTRA_OBRA = {'tema': ['Debe pertenecer a la obra del post.']}
ERROR_IMAGEN_Y_GALERIA = {'imagenes': ['Envía una imagen o una galería, no ambas.']}
ERROR_DISPOSICION = {'disposicion': ['Esa disposición no es válida para ese número de imágenes.']}
ERROR_NUMERO_COMPARADOS = {'personajes_comparados': ['Una comparativa necesita de 2 a 4 personajes.']}
ERROR_COMPARADO_AJENO = {'personajes_comparados': ['Cada personaje debe pertenecer a la obra o a la obra comparada.']}


def error_400(detail):
    return Response({'detail': detail}, status=status.HTTP_400_BAD_REQUEST)


def tema_de_otra_obra(tema, obra_id):
    return bool(tema) and tema.obra_id != obra_id