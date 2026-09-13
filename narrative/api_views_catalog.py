from django.contrib.auth.models import User
from django.db.models import Count, Max
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404

from posts.models import Hashtag, Post
from subscriptions.models import Suscripcion
from .models import Obra, ProgresoUsuario, TemaTransversal, UnidadNarrativa, SolicitudTema
from .serializers import ObraResumenSerializer, UnidadNarrativaSerializer, SolicitudTemaSerializer


def _contexto_suscripcion_obra(user):
    """Contexto compartido por CatalogoObrasAPIView y BuscarAPIView:
    ids_obras_suscritas incluye CUALQUIER nivel de suscripción (obra,
    unidad o tema) -- se usa para decidir si una obra entra en
    Biblioteca. suscripcion_id_por_obra, en cambio, solo mapea
    suscripciones de nivel OBRA COMPLETA (unidad y tema nulos): es lo
    que representa el botón Seguir/Siguiendo de un Lomo de obra, que no
    debe confundirse con seguir un tema o arco concreto de esa obra."""
    todas_las_suscripciones = Suscripcion.objects.filter(usuario=user)

    ids_obras_suscritas = set(todas_las_suscripciones.values_list('obra_id', flat=True))

    suscripciones_de_obra = todas_las_suscripciones.filter(unidad__isnull=True, tema__isnull=True)
    suscripcion_id_por_obra = {s.obra_id: s.id for s in suscripciones_de_obra}

    return {
        'ids_obras_suscritas': ids_obras_suscritas,
        'suscripcion_id_por_obra': suscripcion_id_por_obra,
    }


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

        return Response({
            'obra': {'id': obra.id, 'titulo': obra.titulo, 'slug': obra.slug},
            'unidades': UnidadNarrativaSerializer(unidades, many=True).data,
            'temas': [{'id': t.id, 'nombre': t.nombre} for t in temas],
        })


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
    """Búsqueda combinada: obras y temas (dominio narrativo, ya existía),
    más usuarios, hashtags y posts (migrado desde global_search.js /
    posts/views/search.py, con una corrección de seguridad importante:
    la búsqueda de posts original NO aplicaba visible_for(), pudiendo
    filtrar texto de posts bloqueados por frontera de spoiler. Aquí se
    corrige exigiendo Post.objects.visible_for(request.user) como base.

    Las vistas Django clásicas (mentions_search, hashtags_search,
    global_search) NO se tocan ni se retiran -- siguen sirviendo a las
    plantillas HTML heredadas hasta que se migren a React."""

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
                }
                for t in temas
            ],
            'usuarios': [_usuario_data(u) for u in usuarios],
            'hashtags': [{'name': h.name} for h in hashtags],
            'posts': [_post_data(p) for p in posts],
        })