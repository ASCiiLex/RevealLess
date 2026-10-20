from django.contrib.auth.models import User
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.http import Http404
from django.utils.text import slugify
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from posts.models import Hashtag
from subscriptions.models import Suscripcion
from ..models import Categoria, Obra, ProgresoUsuario, TemaTransversal, UnidadNarrativa
from ..serializers import ObraResumenSerializer
from ..services.personajes import progreso_por_obra
from .comun import contexto_suscripcion_obra, suscripcion_id_por_tema

AVATAR_POR_DEFECTO = '/static/img/default_profile.jpg'


def _usuario_data(user):
    avatar = user.profile.image_url if hasattr(user, 'profile') else AVATAR_POR_DEFECTO
    return {'username': user.username, 'avatar_url': avatar}


def _tema_data(tema, ids_por_tema):
    return {
        'id': tema.id,
        'nombre': tema.nombre,
        'obra_id': tema.obra_id,
        'obra_titulo': tema.obra.titulo,
        'obra_slug': tema.obra.slug,
        'suscrito': tema.id in ids_por_tema,
        'suscripcion_id': ids_por_tema.get(tema.id),
    }


def _suscripcion_id_por_unidad(user):
    return dict(
        Suscripcion.objects.filter(usuario=user, unidad__isnull=False).values_list('unidad_id', 'id')
    )


def _arco_data(unidad, ids_por_unidad):
    return {
        'id': unidad.id,
        'nombre': unidad.nombre,
        'padre_nombre': unidad.padre.nombre if unidad.padre_id else None,
        'obra_id': unidad.obra_id,
        'obra_titulo': unidad.obra.titulo,
        'obra_slug': unidad.obra.slug,
        'suscrito': unidad.id in ids_por_unidad,
        'suscripcion_id': ids_por_unidad.get(unidad.id),
    }


def _respuesta(obras=(), arcos=(), categorias=(), temas=(), usuarios=(), hashtags=()):
    return {
        'obras': list(obras),
        'arcos': list(arcos),
        'categorias': list(categorias),
        'temas': list(temas),
        'usuarios': list(usuarios),
        'hashtags': list(hashtags),
    }


def buscar_obras(q, limite):
    """Título o slug (el slug tolera tildes y espacios: 'peliculas' encuentra 'Películas').
    Primero los títulos que empiezan por la búsqueda; orden estable por título."""
    filtro = Q(titulo__icontains=q)
    q_slug = slugify(q)
    if q_slug:
        filtro |= Q(slug__icontains=q_slug)
    return (
        Obra.objects.filter(filtro)
        .annotate(relevancia=Case(
            When(titulo__istartswith=q, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        ))
        .order_by('relevancia', 'titulo')[:limite]
    )


def buscar_arcos(user, q, limite):
    """Bloques (unidades con hijos, nunca episodios) que el usuario ya ha empezado:
    el nombre de uno aún no alcanzado podría adelantar algo."""
    progreso = progreso_por_obra(user)
    if not progreso:
        return []
    empezados = Q(pk__in=[])
    for obra_id, orden in progreso.items():
        empezados |= Q(obra_id=obra_id, orden_inicio__lte=orden)
    return (
        UnidadNarrativa.objects
        .filter(empezados, nombre__icontains=q, hijos__isnull=False)
        .select_related('obra', 'padre')
        .distinct()
        .order_by('obra__titulo', 'orden_inicio')[:limite]
    )


class BuscarAPIView(APIView):
    """Descubre qué seguir: obras, arcos ya empezados, categorías, temas, usuarios y hashtags.
    Sin publicaciones: el contenido se lee en el feed, con su filtro anti-spoiler."""

    permission_classes = [IsAuthenticated]

    MIN_CARACTERES = 2
    LIMITE_POR_TIPO = 5
    # Las franquicias con muchas obras (Star Wars: 9) no deben quedar recortadas.
    LIMITE_OBRAS = 10

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        limite = self.LIMITE_POR_TIPO

        if len(q) < self.MIN_CARACTERES:
            sugeridos = Hashtag.objects.annotate(num_posts=Count('posts')).order_by('-num_posts')[:limite]
            return Response(_respuesta(hashtags=[{'name': h.name} for h in sugeridos]))

        ids_por_tema = suscripcion_id_por_tema(request.user)
        ids_por_unidad = _suscripcion_id_por_unidad(request.user)

        obras = buscar_obras(q, self.LIMITE_OBRAS)
        arcos = buscar_arcos(request.user, q, limite)
        categorias = (
            Categoria.objects.filter(nombre__icontains=q)
            .annotate(total_obras=Count('obras'))
            .order_by('nombre')[:limite]
        )
        temas = TemaTransversal.objects.filter(nombre__icontains=q).select_related('obra')[:limite]
        usuarios = (
            User.objects.filter(username__icontains=q)
            .select_related('profile').order_by('username')[:limite]
        )
        hashtags = Hashtag.objects.filter(name__icontains=q).order_by('name')[:limite]

        return Response(_respuesta(
            obras=ObraResumenSerializer(
                obras, many=True, context=contexto_suscripcion_obra(request.user),
            ).data,
            arcos=[_arco_data(a, ids_por_unidad) for a in arcos],
            categorias=[{'id': c.id, 'nombre': c.nombre, 'total_obras': c.total_obras} for c in categorias],
            temas=[_tema_data(t, ids_por_tema) for t in temas],
            usuarios=[_usuario_data(u) for u in usuarios],
            hashtags=[{'name': h.name} for h in hashtags],
        ))


class ArcoAPIView(APIView):
    """Cabecera del feed filtrado por un arco. 404 si aún no se ha empezado,
    igual que si no existiera: la URL directa no debe revelar su nombre."""

    permission_classes = [IsAuthenticated]

    def get(self, request, unidad_id):
        unidad = get_object_or_404(UnidadNarrativa.objects.select_related('obra', 'padre'), id=unidad_id)
        progreso = (
            ProgresoUsuario.objects.filter(usuario=request.user, obra_id=unidad.obra_id)
            .values_list('orden_absoluto', flat=True).first()
        )
        if progreso is None or progreso < unidad.orden_inicio:
            raise Http404
        return Response(_arco_data(unidad, _suscripcion_id_por_unidad(request.user)))