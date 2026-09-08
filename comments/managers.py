from django.db import models
from django.db.models import F, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from posts.models import Post
from narrative.models import ProgresoUsuario


class CommentQuerySet(models.QuerySet):
    def visible_for(self, user):
        if not user.is_authenticated:
            return self.none()

        visible_posts = Post.objects.visible_for(user)

        progreso_lector = ProgresoUsuario.objects.filter(
            usuario=user, obra=OuterRef('post__obra')
        ).values('orden_absoluto')[:1]

        return self.annotate(
            frontera_efectiva_orden=Coalesce('frontera_orden', 'post__frontera_orden'),
            progreso_lector=Coalesce(
                Subquery(progreso_lector, output_field=models.IntegerField()),
                Value(0),
            ),
        ).filter(
            post__in=visible_posts,
        ).filter(
            Q(user=user) | Q(progreso_lector__gte=F('frontera_efectiva_orden'))
        )