from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ia.models import UsoIA
from narrative.ai_assistant import TIMEOUT_SUGERENCIA, etiqueta_unidad, proponer_clasificacion
from narrative.models import Obra, ProgresoUsuario, UnidadNarrativa
from ..videos import VideoNoValido, resolver_video, texto_con_video
from .comun import error_400, frontera_minima, frontera_sin_previa_cerrada


def _unidad_json(unidad):
    return {'id': unidad.id, 'etiqueta': etiqueta_unidad(unidad)} if unidad else None


def _texto_para_ia(texto, video_url):
    """Con vídeo, la IA ve también su título y canal. Un enlace no válido no impide sugerir:
    el error se le muestra al autor al publicar."""
    if not video_url:
        return texto
    try:
        video = resolver_video(video_url)
    except VideoNoValido:
        return texto
    return texto_con_video(texto, video['titulo'], video['canal'])


# Cada llamada cuesta tokens de la API: límite por usuario.
@method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True), name='post')
class SugerirFronteraAPIView(APIView):
    """Propuesta de la IA antes de publicar. Revisa el autor, así que se devuelve aunque no supere
    el umbral (fiable=False). Los hechos que la justifican nunca salen: serían spoilers para el autor.
    `desde`: obra desde la que se publica; para la obra cruzada basta con tener progreso en ella.
    La propuesta se ajusta como al publicar: nunca por debajo de la parte elegida ni en un previo cerrado."""

    permission_classes = [IsAuthenticated]

    def post(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        desde = (request.data.get('desde') or '').strip()
        slugs = {obra.slug, desde} - {''}
        if not ProgresoUsuario.objects.filter(usuario=request.user, obra__slug__in=slugs).exists():
            return Response(
                {'detail': 'progreso_requerido', 'obra_slug': obra.slug},
                status=status.HTTP_409_CONFLICT,
            )

        texto = (request.data.get('text') or '').strip()
        if not texto:
            return error_400({'text': ['Escribe el texto antes de pedir una sugerencia.']})

        referencia_id = str(request.data.get('referencia_narrativa') or '')
        referencia = (
            UnidadNarrativa.objects.select_related('padre').filter(pk=int(referencia_id), obra=obra).first()
            if referencia_id.isdigit() else None
        )

        sugerencia = proponer_clasificacion(
            _texto_para_ia(texto, (request.data.get('video_url') or '').strip()),
            obra, referencia, timeout=TIMEOUT_SUGERENCIA,
            usuario=request.user, funcion=UsoIA.FUNCION_SUGERENCIA,
        )
        frontera = frontera_sin_previa_cerrada(frontera_minima(sugerencia.frontera_spoiler, referencia))
        return Response({
            'frontera': _unidad_json(frontera),
            'parte': None if referencia or frontera is None else _unidad_json(sugerencia.parte),
            'confianza': round(sugerencia.confianza, 2),
            'fiable': sugerencia.es_utilizable,
        })