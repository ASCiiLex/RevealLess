from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from feed.utils import get_user_feed
from posts.models import Post
from .models import Obra, ProgresoUsuario, UnidadNarrativa
from .serializers import PostSerializer, ProgresoUsuarioSerializer, UnidadNarrativaSerializer
from .services import actualizar_progreso


class FeedAPIView(generics.ListAPIView):
    """Feed anti-spoiler: mismos datos que feed_view, ya filtrados por el
    motor de visibilidad."""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        base_posts = get_user_feed(user)
        own_posts = Post.objects.filter(author=user)
        return (base_posts | own_posts).distinct().visible_for(user).order_by('-created_at')


class ProgresoAPIView(APIView):
    """GET: unidades de la obra + progreso actual del usuario (o null).
    POST: actualiza el progreso. Body JSON: {"unidad_actual": <id>}."""
    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        unidades = UnidadNarrativa.objects.filter(obra=obra).order_by('orden_inicio')
        progreso = ProgresoUsuario.objects.filter(usuario=request.user, obra=obra).first()

        return Response({
            'obra': {'titulo': obra.titulo, 'slug': obra.slug},
            'unidades': UnidadNarrativaSerializer(unidades, many=True).data,
            'progreso': ProgresoUsuarioSerializer(progreso).data if progreso else None,
        })

    def post(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        unidad = get_object_or_404(
            UnidadNarrativa, id=request.data.get('unidad_actual'), obra=obra
        )

        try:
            progreso = actualizar_progreso(request.user, obra, unidad)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ProgresoUsuarioSerializer(progreso).data)