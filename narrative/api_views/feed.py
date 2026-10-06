from django.db.models import Q
from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from posts.models import Post
from subscriptions.models import Suscripcion
from subscriptions.services import (
    filtro_posts_silenciados,
    filtro_posts_suscripciones,
    q_posts_de_personaje,
)
from ..models import TemaTransversal
from ..serializers import PostSerializer
from .comun import entero_o_none, ids_familia


class FeedAPIView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        return {'request': self.request}

    def get_queryset(self):
        user = self.request.user
        params = self.request.query_params

        # Comparativas: también llegan a quien sigue la obra cruzada (visible_for decide las fronteras).
        obras_seguidas = Suscripcion.objects.filter(
            usuario=user, activa=True, obra__isnull=False, unidad__isnull=True, tema__isnull=True,
        ).values('obra_id')

        condiciones_del_feed = (
            Q(author=user)
            | Q(author__in=user.following.values_list('followed', flat=True))
            | filtro_posts_suscripciones(user)
            | Q(obra_cruzada_id__in=obras_seguidas)
        )

        queryset = (
            Post.objects
            .filter(condiciones_del_feed)
            .exclude(filtro_posts_silenciados(user))
            .distinct()
            .select_related(
                'author__profile',
                'obra',
                'obra_cruzada',
                'referencia_narrativa__padre',
                'referencia_narrativa__obra',
                'frontera_spoiler__padre',
                'frontera_spoiler__obra',
                'frontera_cruzada__padre',
                'frontera_cruzada__obra',
            )
            .prefetch_related(
                'imagenes', 'temas_transversales', 'comparaciones__personaje', 'comparaciones__solicitud',
            )
            .visible_for(user)
            .with_feed_stats()
        )

        obra_id = entero_o_none(params.get('obra'), 'obra')
        if obra_id is not None:
            queryset = queryset.filter(Q(obra_id=obra_id) | Q(obra_cruzada_id=obra_id))

        hashtag = params.get('hashtag')
        if hashtag is not None:
            queryset = queryset.filter(post_hashtags__hashtag__name=hashtag)

        tema_id = entero_o_none(params.get('tema'), 'tema')
        if tema_id is not None:
            tema = get_object_or_404(TemaTransversal.objects.select_related('obra'), id=tema_id)
            queryset = queryset.filter(
                temas_transversales__nombre=tema.nombre,
                temas_transversales__obra_id__in=ids_familia(tema.obra),
            )

        personaje_id = entero_o_none(params.get('personaje'), 'personaje')
        if personaje_id is not None:
            queryset = queryset.filter(q_posts_de_personaje(personaje_id))

        return queryset.order_by('-created_at')