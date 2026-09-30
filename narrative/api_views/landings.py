from django.db.models import Max, Min, Q
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from subscriptions.models import Suscripcion
from ..models import Categoria, Obra, Personaje, ProgresoUsuario, TemaTransversal
from ..serializers import ObraLandingSerializer, ObraResumenSerializer
from .comun import contexto_suscripcion_obra, ids_familia, suscripcion_id_por_tema


def _total_suscriptores(**filtro):
    return Suscripcion.objects.filter(**filtro).values('usuario').distinct().count()


def personajes_visibles(obra, progreso):
    """Solo personajes cuya primera aparición en esta obra ya alcanzó el usuario:
    listar uno que aún no ha salido sería en sí mismo un spoiler."""
    if not progreso:
        return []
    return list(
        Personaje.objects.filter(unidades__obra=obra)
        .annotate(primera_aparicion=Min('unidades__orden_fin', filter=Q(unidades__obra=obra)))
        .filter(primera_aparicion__lte=progreso.orden_absoluto)
        .distinct()
        .order_by('nombre')
    )


class ObraLandingAPIView(APIView):
    """Sinopsis, categorías, progreso, suscriptores, temas, obras relacionadas y personajes ya conocidos."""

    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(
            Obra.objects.prefetch_related('categorias').annotate(longitud_total=Max('unidades__orden_fin')),
            slug=obra_slug,
        )
        progreso = ProgresoUsuario.objects.filter(usuario=request.user, obra=obra).first()

        contexto = {
            **contexto_suscripcion_obra(request.user),
            'progreso': progreso,
            'longitud_total': obra.longitud_total,
            'total_suscriptores': _total_suscriptores(obra=obra),
            'suscripcion_id_por_tema': suscripcion_id_por_tema(request.user),
            'personajes_visibles': personajes_visibles(obra, progreso),
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


class CategoriaLandingAPIView(APIView):
    """Obras de una categoría con el mismo formato que los lomos del carrusel."""

    permission_classes = [IsAuthenticated]

    def get(self, request, categoria_id):
        categoria = get_object_or_404(Categoria, id=categoria_id)
        obras = (
            categoria.obras.prefetch_related('categorias')
            .annotate(longitud_total=Max('unidades__orden_fin'))
            .order_by('titulo')
        )
        contexto = {
            'progreso_por_obra': dict(
                ProgresoUsuario.objects.filter(usuario=request.user).values_list('obra_id', 'orden_absoluto')
            ),
            **contexto_suscripcion_obra(request.user),
        }
        datos = ObraResumenSerializer(obras, many=True, context=contexto).data

        return Response({
            'id': categoria.id,
            'nombre': categoria.nombre,
            'total_obras': len(datos),
            'obras': datos,
        })