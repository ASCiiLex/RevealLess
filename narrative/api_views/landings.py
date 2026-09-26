from django.db.models import Max
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from subscriptions.models import Suscripcion
from ..models import Obra, ProgresoUsuario, TemaTransversal
from ..serializers import ObraLandingSerializer
from .comun import contexto_suscripcion_obra, ids_familia, suscripcion_id_por_tema


def _total_suscriptores(**filtro):
    return Suscripcion.objects.filter(**filtro).values('usuario').distinct().count()


class ObraLandingAPIView(APIView):
    """Sinopsis, categorías, progreso, suscriptores (cualquier nivel) y temas con su estado de suscripción."""

    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(
            Obra.objects.annotate(longitud_total=Max('unidades__orden_fin')),
            slug=obra_slug,
        )

        contexto = {
            **contexto_suscripcion_obra(request.user),
            'progreso': ProgresoUsuario.objects.filter(usuario=request.user, obra=obra).first(),
            'longitud_total': obra.longitud_total,
            'total_suscriptores': _total_suscriptores(obra=obra),
            'suscripcion_id_por_tema': suscripcion_id_por_tema(request.user),
        }

        return Response(ObraLandingSerializer(obra, context=contexto).data)


class TemaLandingAPIView(APIView):
    """Agrupa por nombre los temas de la misma franquicia en tiempo de consulta.
    'Seguir' actúa siempre sobre el TemaTransversal concreto de la URL."""

    permission_classes = [IsAuthenticated]

    def get(self, request, tema_id):
        tema = get_object_or_404(TemaTransversal.objects.select_related('obra'), id=tema_id)
        temas_grupo = list(
            TemaTransversal.objects
            .filter(nombre=tema.nombre, obra_id__in=ids_familia(tema.obra))
            .select_related('obra')
        )

        suscripcion = Suscripcion.objects.filter(usuario=request.user, tema__in=temas_grupo).first()

        return Response({
            'id': tema.id,
            'nombre': tema.nombre,
            'obra_slug': tema.obra.slug,
            'obras': [
                {'id': t.obra.id, 'titulo': t.obra.titulo, 'slug': t.obra.slug, 'tema_id': t.id}
                for t in temas_grupo
            ],
            'suscrito': suscripcion is not None,
            'suscripcion_id': suscripcion.id if suscripcion else None,
            'total_suscriptores': _total_suscriptores(tema__in=temas_grupo),
        })