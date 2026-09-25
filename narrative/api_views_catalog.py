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
        # select_related('padre'): sin esto, UnidadNarrativaSerializer.
        # get_padre_etiqueta() disparaba una consulta por cada unidad
        # (N+1) -- con obras de cientos de capitulos (importados via
        # Jikan) esto tardaba mas de 1s por peticion.
        unidades = UnidadNarrativa.objects.filter(obra=obra).select_related('padre').order_by('orden_inicio')
        temas = TemaTransversal.objects.filter(obra=obra).order_by('nombre')
        relacionadas = obra.obras_relacionadas()

        return Response({
            'obra': {'id': obra.id, 'titulo': obra.titulo, 'slug': obra.slug},
            'unidades': UnidadNarrativaSerializer(unidades, many=True).data,
            'temas': [{'id': t.id, 'nombre': t.nombre} for t in temas],
            'obras_relacionadas': [
                {'id': o.id, 'slug': o.slug, 'titulo': o.titulo} for o in relacionadas
            ],
        })


class UnidadesBuscarAPIView(APIView):
    """Busqueda de unidades narrativas de una obra por texto, para
    BuscadorLocal (referencia/progreso/frontera en el formulario de
    publicar). Evita cargar de golpe obras con miles de unidades
    (One Piece: 1229) -- ObraDetalleAPIView sigue sirviendo el listado
    completo para el arbol de progreso, que si necesita el conjunto
    entero de una vez."""

    permission_classes = [IsAuthenticated]
    LIMITE = 30

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        q = request.query_params.get('q', '').strip()

        unidades = UnidadNarrativa.objects.filter(obra=obra)
        if q:
            unidades = unidades.filter(nombre__icontains=q)
        unidades = unidades.order_by('orden_inicio')[:self.LIMITE]

        return Response({'unidades': UnidadNarrativaSerializer(unidades, many=True).data})


class ObraContextoPublicarAPIView(APIView):
    """Version ligera de ObraDetalleAPIView para el formulario de
    publicar: solo temas y obras relacionadas, sin las unidades (que en
    obras grandes -- One Piece: 1229 -- eran el grueso real del peso y
    tiempo de la respuesta, y ya no las usa este formulario desde que
    BuscadorLocal busca en el servidor)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        temas = TemaTransversal.objects.filter(obra=obra).order_by('nombre')

        return Response({
            'obra': {'id': obra.id, 'titulo': obra.titulo, 'slug': obra.slug},
            'temas': [{'id': t.id, 'nombre': t.nombre} for t in temas],
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


class TemaLandingAPIView(APIView):
    """Landing de un tema transversal (Plan A): agrupa por nombre todos
    los TemaTransversal de la misma franquicia (obra + sus continuidades
    relacionadas via adapta_a/adaptaciones), en tiempo de consulta, sin
    cambiar el modelo -- cada TemaTransversal sigue perteneciendo a una
    unica obra. El motor de visibilidad no se ve afectado: cada post
    sigue blindado por su propia referencia_narrativa/frontera_spoiler,
    atada a su propia obra. 'Seguir' siempre actua sobre el
    TemaTransversal concreto de la URL (obra_slug/id devueltos), no
    sobre el grupo -- Suscripcion exige un TemaTransversal real."""

    permission_classes = [IsAuthenticated]

    def get(self, request, tema_id):
        tema = get_object_or_404(TemaTransversal.objects.select_related('obra'), id=tema_id)
        familia_ids = [tema.obra_id] + [o.id for o in tema.obra.obras_relacionadas()]
        temas_grupo = list(
            TemaTransversal.objects.filter(nombre=tema.nombre, obra_id__in=familia_ids)
            .select_related('obra')
        )

        suscripcion = Suscripcion.objects.filter(usuario=request.user, tema__in=temas_grupo).first()
        total_suscriptores = Suscripcion.objects.filter(tema__in=temas_grupo).values('usuario').distinct().count()

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
            'total_suscriptores': total_suscriptores,
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