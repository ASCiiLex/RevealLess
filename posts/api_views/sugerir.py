from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from narrative.ai_assistant import TIMEOUT_SUGERENCIA, etiqueta_unidad, proponer_clasificacion
from narrative.models import Obra, ProgresoUsuario, UnidadNarrativa
from .comun import error_400


def _unidad_json(unidad):
    return {'id': unidad.id, 'etiqueta': etiqueta_unidad(unidad)} if unidad else None


class SugerirFronteraAPIView(APIView):
    """Propuesta de la IA antes de publicar: frontera, parte (si el autor no la eligió) y revelaciones
    que la justifican. Sin propuesta fiable, frontera=None; las revelaciones se devuelven igual como pista."""

    permission_classes = [IsAuthenticated]

    def post(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        if not ProgresoUsuario.objects.filter(usuario=request.user, obra=obra).exists():
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

        sugerencia = proponer_clasificacion(texto, obra, referencia, timeout=TIMEOUT_SUGERENCIA)
        utilizable = sugerencia.es_utilizable
        return Response({
            'frontera': _unidad_json(sugerencia.frontera_spoiler) if utilizable else None,
            'parte': _unidad_json(sugerencia.parte) if utilizable and not referencia else None,
            'confianza': round(sugerencia.confianza, 2),
            'revelaciones': [
                {'hecho': r.hecho, 'etiqueta': etiqueta_unidad(r.unidad)} for r in sugerencia.revelaciones
            ],
        })