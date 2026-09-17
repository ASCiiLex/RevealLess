from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from posts.models import Post
from subscriptions.services import filtro_posts_suscripciones, filtro_posts_silenciados
from .models import Obra, ProgresoUsuario, UnidadNarrativa
from .serializers import PostSerializer, ProgresoUsuarioSerializer, UnidadNarrativaSerializer
from .services import actualizar_progreso, SaltoGrandeRequiereConfirmacion


class FeedAPIView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        return {'request': self.request}

    def get_queryset(self):
        user = self.request.user
        followed_users = user.following.values_list('followed', flat=True)
        subscription_q = filtro_posts_suscripciones(user)
        silenciado_q = filtro_posts_silenciados(user)

        condiciones_del_feed = (
            Q(author=user)
            | Q(author__in=followed_users)
            | subscription_q
        )

        queryset = (
            Post.objects
            .filter(condiciones_del_feed)
            .exclude(silenciado_q)
            .distinct()
            .select_related(
                'author',
                'obra',
                'referencia_narrativa',
                'referencia_narrativa__padre',
            )
            .visible_for(user)
            .with_feed_stats()
        )

        obra_id = self.request.query_params.get('obra')
        if obra_id is not None:
            queryset = queryset.filter(obra_id=obra_id)

        hashtag = self.request.query_params.get('hashtag')
        if hashtag is not None:
            queryset = queryset.filter(post_hashtags__hashtag__name=hashtag)

        return queryset.order_by('-created_at')


class ProgresoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        unidades = UnidadNarrativa.objects.filter(obra=obra).order_by('orden_inicio')
        progreso = ProgresoUsuario.objects.filter(
            usuario=request.user,
            obra=obra,
        ).first()

        return Response({
            'obra': {'titulo': obra.titulo, 'slug': obra.slug},
            'unidades': UnidadNarrativaSerializer(unidades, many=True).data,
            'progreso': ProgresoUsuarioSerializer(progreso).data if progreso else None,
        })

    def post(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        unidad = get_object_or_404(
            UnidadNarrativa,
            id=request.data.get('unidad_actual'),
            obra=obra,
        )
        confirmado = bool(request.data.get('confirmado', False))

        try:
            progreso = actualizar_progreso(
                request.user,
                obra,
                unidad,
                confirmado=confirmado,
            )
        except ValueError as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except SaltoGrandeRequiereConfirmacion as exc:
            return Response({
                'detail': str(exc),
                'requiere_confirmacion': True,
                'salto': exc.salto,
            }, status=status.HTTP_409_CONFLICT)

        return Response(ProgresoUsuarioSerializer(progreso).data)