from django.contrib.auth.models import User
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.utils.text import slugify
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from posts.models import Hashtag, Post
from ..models import Obra, TemaTransversal
from ..serializers import ObraResumenSerializer
from .comun import contexto_suscripcion_obra, suscripcion_id_por_tema

AVATAR_POR_DEFECTO = '/static/img/default_profile.jpg'


def _usuario_data(user):
    avatar = user.profile.image_url if hasattr(user, 'profile') else AVATAR_POR_DEFECTO
    return {'username': user.username, 'avatar_url': avatar}


def _post_data(post):
    return {'id': post.id, 'text': post.text[:140], 'image': post.image_url}


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


class BuscarAPIView(APIView):
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
            return Response({
                'obras': [], 'temas': [], 'usuarios': [], 'posts': [],
                'hashtags': [{'name': h.name} for h in sugeridos],
            })

        ids_por_tema = suscripcion_id_por_tema(request.user)

        obras = buscar_obras(q, self.LIMITE_OBRAS)
        temas = TemaTransversal.objects.filter(nombre__icontains=q).select_related('obra')[:limite]
        usuarios = (
            User.objects.filter(username__icontains=q)
            .select_related('profile').order_by('username')[:limite]
        )
        hashtags = Hashtag.objects.filter(name__icontains=q).order_by('name')[:limite]
        posts = (
            Post.objects.filter(text__icontains=q)
            .visible_for(request.user)
            .order_by('-created_at')[:limite]
        )

        return Response({
            'obras': ObraResumenSerializer(
                obras, many=True, context=contexto_suscripcion_obra(request.user),
            ).data,
            'temas': [_tema_data(t, ids_por_tema) for t in temas],
            'usuarios': [_usuario_data(u) for u in usuarios],
            'hashtags': [{'name': h.name} for h in hashtags],
            'posts': [_post_data(p) for p in posts],
        })