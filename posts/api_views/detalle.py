from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from comments.models import CommentReaction
from comments.serializers import CommentSerializer
from core.reacciones import totales_agrupados
from likes.models import PostReaction
from narrative.serializers import PostSerializer
from ..models import Post
from ..selectors import get_sorted_comments

CLAVES_COMENTARIO = tuple(c for c, _ in CommentReaction.REACTION_CHOICES)


class PostDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, post_id):
        post = get_object_or_404(Post.objects.visible_for(request.user), id=post_id)
        comments = get_sorted_comments(request.user, post, request.query_params.get('sort', 'recent'))

        reaction_map = {}
        post_reaction = None
        if request.user.is_authenticated:
            reaction_map = dict(
                CommentReaction.objects.filter(
                    user=request.user, comment__post=post
                ).values_list('comment_id', 'reaction')
            )
            post_reaction = (
                PostReaction.objects.filter(user=request.user, post=post)
                .values_list('reaction', flat=True).first()
            )

        # Totales de todos los comentarios del post (respuestas incluidas) en una consulta.
        totales_comentarios = totales_agrupados(
            CommentReaction.objects.filter(comment__post=post), 'comment_id', CLAVES_COMENTARIO
        )

        return Response({
            'post': PostSerializer(post, context={'request': request}).data,
            'post_reaction': post_reaction,
            'comments': CommentSerializer(
                comments, many=True,
                context={
                    'reaction_map': reaction_map,
                    'reacciones_totales': totales_comentarios,
                    'request': request,
                },
            ).data,
        })