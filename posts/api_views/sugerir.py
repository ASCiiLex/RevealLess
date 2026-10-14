from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from narrative.ai_assistant import proponer_clasificacion
from narrative.models import Obra, ProgresoUsuario, UnidadNarrativa
from .comun import error_400


def _etiqueta(unidad):
    return f'{unidad.padre.nombre} · {unidad.nombre}' if unidad.padre_id else unidad.nombre


class SugerirFronteraAPIView(APIView):
    """Propuesta de frontera de la IA antes de publicar: el autor la ve y decide.
    Sin propuesta fiable devuelve frontera=None; al publicar se aplica el fallback de siempre."""

    permission_classes = [IsAuthenticated]

    def post(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        progreso = (
            ProgresoUsuario.objects.filter(usuario=request.user, obra=obra)
            .select_related('unidad_actual').first()
        )
        if not progreso:
            return Response(
                {'detail': 'progreso_requerido', 'obra_slug': obra.slug},
                status=status.HTTP_409_CONFLICT,
            )

        texto = (request.data.get('text') or '').strip()
        if not texto:
            return error_400({'text': ['Escribe el texto antes de pedir una sugerencia.']})

        referencia_id = str(request.data.get('referencia_narrativa') or '')
        referencia = (
            UnidadNarrativa.objects.filter(pk=int(referencia_id), obra=obra).first()
            if referencia_id.isdigit() else None
        )

        sugerencia = proponer_clasificacion(texto, obra, progreso.unidad_actual, referencia)
        if not sugerencia.es_utilizable:
            return Response({'frontera': None, 'confianza': round(sugerencia.confianza, 2)})

        unidad = sugerencia.frontera_spoiler
        return Response({
            'frontera': {'id': unidad.id, 'etiqueta': _etiqueta(unidad)},
            'confianza': round(sugerencia.confianza, 2),
        })