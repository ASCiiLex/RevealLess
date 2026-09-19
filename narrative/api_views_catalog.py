from django.contrib.auth.models import User
from django.db.models import Count, Max
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404

from posts.models import Hashtag, Post
from subscriptions.models import Suscripcion
from .models import Obra, ProgresoUsuario, TemaTransversal, UnidadNarrativa, SolicitudTema
from .serializers import (
    ObraResumenSerializer, UnidadNarrativaSerializer, SolicitudTemaSerializer,
    ObraLandingSerializer,
)


def _contexto_suscripcion_obra(user):
    todas_las_suscripciones = Suscripcion.objects.filter(usuario=user)

    ids_obras_suscritas = set(todas_las_suscripciones.values_list('obra_id', flat=True))

    suscripciones_de_obra = todas_las_suscripciones.filter(unidad__isnull=True, tema__isnull=True)
    suscripcion_id_por_obra = {s.obra_id: s.id for s in suscripciones_de_obra}

    return {
        'ids_obras_suscritas': ids_obras_suscritas,
        'suscripcion_id_por_obra': suscripcion_id_por_obra,
    }


def _suscripcion_id_por_tema(user):
    suscripciones_de_tema = Suscripcion.objects.filter(usuario=user, tema__isnull=False)
    return {s.tema_id: s.id for s in suscripciones_de_tema}


def _obras_relacionadas(obra):
    """Continuidades de la misma franquicia (MVP del blindaje): la obra
    de la que esta se adapta, y las que se adaptan de esta. Puramente
    informativo para poblar el selector de 'obra cruzada' en posts/
    comentarios -- no implica ningun mapeo de equivalencia entre las
    escalas de orden de cada una."""
    relacionadas = []
    if obra.adapta_a_id:
        relacionadas.append(obra.adapta_a)
    relacionadas.extend(obra.adaptaciones.all())
    return relacionadas


class CatalogoObrasAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        progresos = ProgresoUsuario.objects.filter(usuario=user)
        progreso_por_obra = {p.obra_id: p.orden_absoluto for p in progresos}

        contexto_suscripcion = _contexto_suscripcion_obra(user)
        ids_biblioteca = set(progreso_por_obra.keys()) | contexto_suscripcion['ids_obras_suscritas']

        todas = Obra.objects.prefetch_related('categorias').annotate(
            longitud_total=Max('unidades__orden_fin')
        )
        biblioteca = todas.filter(id__in=ids_biblioteca)
        descubrir = todas.exclude(id__in=ids_biblioteca)

        contexto = {'progreso_por_obra': progreso_por_obra, **contexto_suscripcion}

        return Response({
            'biblioteca': ObraResumenSerializer(biblioteca, many=True, context=contexto).data,
            'descubrir': ObraResumenSerializer(descubrir, many=True, context=contexto).data,
        })


class ObraDetalleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        unidades = UnidadNarrativa.objects.filter(obra=obra).order_by('orden_inicio')
        temas = TemaTransversal.objects.filter(obra=obra).order_by('nombre')
        relacionadas = _obras_relacionadas(obra)

        return Response({
            'obra': {'id': obra.id, 'titulo': obra.titulo, 'slug': obra.slug},
            'unidades': UnidadNarrativaSerializer(unidades, many=True).data,
            'temas': [{'id': t.id, 'nombre': t.nombre} for t in temas],
            'obras_relacionadas': [
                {'id': o.id, 'slug': o.slug, 'titulo': o.titulo} for o in relacionadas
            ],
        })


class ObraLandingAPIView(APIView):
    """Endpoint dedicado a la landing de obra: sinopsis, categorias,
    progreso del usuario, total de suscriptores (cualquier nivel:
    obra/unidad/tema, todos cuentan como interes por la obra), y sus
    temas transversales con el estado de suscripcion de cada uno."""

    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(
            Obra.objects.annotate(longitud_total=Max('unidades__orden_fin')),
            slug=obra_slug,
        )

        contexto_suscripcion = _contexto_suscripcion_obra(request.user)
        progreso = ProgresoUsuario.objects.filter(usuario=request.user, obra=obra).first()
        total_suscriptores = Suscripcion.objects.filter(obra=obra).values('usuario').distinct().count()

        contexto = {
            **contexto_suscripcion,
            'progreso': progreso,
            'longitud_total': obra.longitud_total,
            'total_suscriptores': total_suscriptores,
            'suscripcion_id_por_tema': _suscripcion_id_por_tema(request.user),
        }

        return Response(ObraLandingSerializer(obra, context=contexto).data)


class SolicitudTemaListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        solicitudes = SolicitudTema.objects.filter(usuario=request.user).select_related('obra')
        return Response(SolicitudTemaSerializer(solicitudes, many=True).data)

    def post(self, request):
        serializer = SolicitudTemaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(usuario=request.user)
        return Response(serializer.data, status=201)


def _usuario_data(user):
    avatar = (
        user.profile.image_url
        if hasattr(user, 'profile')
        else '/static/img/default_profile.jpg'
    )
    return {'username': user.username, 'avatar_url': avatar}


def _post_data(post):
    return {'id': post.id, 'text': post.text[:140], 'image': post.image_url}


class BuscarAPIView(APIView):
    permission_classes = [IsAuthenticated]

    MIN_CARACTERES = 2
    LIMITE_POR_TIPO = 5

    def get(self, request):
        q = request.query_params.get('q', '').strip()

        if len(q) < self.MIN_CARACTERES:
            hashtags_sugeridos = Hashtag.objects.annotate(
                num_posts=Count('posts')
            ).order_by('-num_posts')[:self.LIMITE_POR_TIPO]
            return Response({
                'obras': [],
                'temas': [],
                'usuarios': [],
                'hashtags': [{'name': h.name} for h in hashtags_sugeridos],
                'posts': [],
            })

        contexto_suscripcion = _contexto_suscripcion_obra(request.user)
        suscripcion_id_por_tema = _suscripcion_id_por_tema(request.user)

        obras = Obra.objects.filter(titulo__icontains=q)[:self.LIMITE_POR_TIPO]
        temas = TemaTransversal.objects.filter(nombre__icontains=q).select_related('obra')[:self.LIMITE_POR_TIPO]

        usuarios = User.objects.filter(
            username__icontains=q
        ).select_related('profile').order_by('username')[:self.LIMITE_POR_TIPO]

        hashtags = Hashtag.objects.filter(name__icontains=q).order_by('name')[:self.LIMITE_POR_TIPO]

        posts = (
            Post.objects
            .filter(text__icontains=q)
            .visible_for(request.user)
            .select_related('author', 'obra')
            .order_by('-created_at')[:self.LIMITE_POR_TIPO]
        )

        return Response({
            'obras': ObraResumenSerializer(obras, many=True, context=contexto_suscripcion).data,
            'temas': [
                {
                    'id': t.id,
                    'nombre': t.nombre,
                    'obra_id': t.obra_id,
                    'obra_titulo': t.obra.titulo,
                    'obra_slug': t.obra.slug,
                    'suscrito': t.id in suscripcion_id_por_tema,
                    'suscripcion_id': suscripcion_id_por_tema.get(t.id),
                }
                for t in temas
            ],
            'usuarios': [_usuario_data(u) for u in usuarios],
            'hashtags': [{'name': h.name} for h in hashtags],
            'posts': [_post_data(p) for p in posts],
        })