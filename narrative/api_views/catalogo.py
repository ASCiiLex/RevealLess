import unicodedata

from django.db.models import Max, Min, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Obra, Personaje, ProgresoUsuario, RelevanciaPersonaje, TemaTransversal, UnidadNarrativa
from ..serializers import ObraResumenSerializer, UnidadNarrativaSerializer
from ..services.fronteras import previa_cerrada
from ..services.personajes import nombres_conocidos, presentacion_personaje
from .comun import (
    contexto_suscripcion_obra,
    es_verdadero,
    ids_biblioteca,
    obra_basica,
    personajes_suscritos_serializados,
    temas_planos,
    temas_suscritos_serializados,
)


def _normalizar(texto):
    descompuesto = unicodedata.normalize('NFKD', texto)
    return ''.join(c for c in descompuesto if not unicodedata.combining(c)).lower().strip()


class CatalogoObrasAPIView(APIView):
    """Biblioteca: obras con progreso o alguna suscripción, más temas y personajes suscritos.
    Descubrir: obras que no sigues enteras. Una obra con progreso pero sin seguir aparece en
    ambas, igual que su contenido en los feeds."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        progreso_por_obra = dict(
            ProgresoUsuario.objects.filter(usuario=request.user).values_list('obra_id', 'orden_absoluto')
        )
        contexto_suscripcion = contexto_suscripcion_obra(request.user)

        todas = Obra.objects.prefetch_related('categorias').annotate(
            longitud_total=Max('unidades__orden_fin')
        )
        contexto = {'progreso_por_obra': progreso_por_obra, **contexto_suscripcion}

        biblioteca = ObraResumenSerializer(
            todas.filter(id__in=ids_biblioteca(request.user)), many=True, context=contexto,
        ).data
        descubrir = ObraResumenSerializer(
            todas.exclude(id__in=list(contexto_suscripcion['suscripcion_id_por_obra'])),
            many=True, context=contexto,
        ).data

        return Response({
            'biblioteca': (
                biblioteca
                + temas_suscritos_serializados(request.user)
                + personajes_suscritos_serializados(request.user)
            ),
            'descubrir': descubrir,
        })


class ObrasPublicarAPIView(APIView):
    """Selector de publicar: solo obras de la biblioteca del usuario y sus temas visibles.
    adapta_a_id permite saber en cliente si dos obras cuentan la misma historia."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        ids = ids_biblioteca(request.user)
        obras = Obra.objects.filter(id__in=ids).order_by('titulo')
        temas = (
            TemaTransversal.objects.visibles_para(request.user)
            .filter(obra_id__in=ids).select_related('obra').order_by('nombre')
        )

        return Response({
            'obras': [
                {**obra_basica(o), 'imagen_url': o.image_url, 'adapta_a_id': o.adapta_a_id}
                for o in obras
            ],
            'temas': [
                {'id': t.id, 'nombre': t.nombre, 'obra_slug': t.obra.slug, 'obra_titulo': t.obra.titulo}
                for t in temas
            ],
        })


class PersonajesPublicarAPIView(APIView):
    """Candidatos para una comparativa: personajes ya aparecidos según el progreso del usuario,
    primero los más relevantes. Se buscan y se muestran solo por los nombres que el lector ya
    ha visto (alias revelados incluidos): buscar por uno aún oculto no debe encontrar nada."""

    permission_classes = [IsAuthenticated]
    LIMITE = 30

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        progreso = ProgresoUsuario.objects.filter(usuario=request.user, obra=obra).first()
        if not progreso:
            return Response({'personajes': []})

        hasta = progreso.orden_absoluto
        nivel = RelevanciaPersonaje.objects.filter(personaje=OuterRef('pk'), obra=obra).values('nivel')[:1]
        candidatos = (
            Personaje.objects
            .filter(unidades__obra=obra)
            .annotate(
                primera=Min('unidades__orden_fin', filter=Q(unidades__obra=obra)),
                nivel_obra=Coalesce(Subquery(nivel), Value(RelevanciaPersonaje.NIVEL_SIN_MARCAR)),
            )
            .filter(primera__lte=hasta)
            .prefetch_related('etapas__visible_tras')
        )

        q = _normalizar(request.query_params.get('q', ''))
        progreso_obra = {obra.id: hasta}
        resultado = []
        for p in candidatos:
            datos = presentacion_personaje(p, progreso_obra, obra_id=obra.id)
            if q:
                nombres = nombres_conocidos(p, obra.id, hasta, p.primera) | {datos['nombre']}
                if not any(q in _normalizar(n) for n in nombres):
                    continue
            resultado.append((p.nivel_obra, datos['nombre'], {'id': p.id, **datos}))

        resultado.sort(key=lambda fila: (-fila[0], fila[1].lower()))
        return Response({
            'personajes': [
                {'id': d['id'], 'nombre': d['nombre'], 'imagen_url': d['imagen_url']}
                for _, _, d in resultado[:self.LIMITE]
            ],
        })


class ObraDetalleAPIView(APIView):
    """Listado completo de unidades para el árbol de progreso."""

    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        unidades = (
            UnidadNarrativa.objects.filter(obra=obra)
            .select_related('padre', 'obra')
            .order_by('orden_inicio')
        )

        return Response({
            'obra': obra_basica(obra),
            'unidades': UnidadNarrativaSerializer(unidades, many=True).data,
            'temas': temas_planos(obra, request.user),
            'obras_relacionadas': [obra_basica(o) for o in obra.obras_relacionadas()],
        })


class UnidadesBuscarAPIView(APIView):
    """Búsqueda por texto para BuscadorLocal: evita cargar obras enteras en el formulario de publicar.
    ?frontera=1: para elegir frontera, sin los previos ya estrenados (siguen valiendo como parte)."""

    permission_classes = [IsAuthenticated]
    LIMITE = 30

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        q = request.query_params.get('q', '').strip()

        unidades = UnidadNarrativa.objects.filter(obra=obra).select_related('padre', 'obra')
        if q:
            unidades = unidades.filter(nombre__icontains=q)
        unidades = list(unidades.order_by('orden_inicio')[:self.LIMITE])
        if es_verdadero(request.query_params.get('frontera')):
            unidades = [u for u in unidades if not previa_cerrada(u)]

        return Response({'unidades': UnidadNarrativaSerializer(unidades, many=True).data})


class ObraContextoPublicarAPIView(APIView):
    """Versión ligera para publicar: solo temas visibles, sin unidades."""

    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        return Response({'obra': obra_basica(obra), 'temas': temas_planos(obra, request.user)})