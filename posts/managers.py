from django.db import models
from django.db.models import F, IntegerField, OuterRef, Q, Subquery, Value, Count
from django.db.models.functions import Coalesce
from narrative.models import ProgresoUsuario


class PostQuerySet(models.QuerySet):
    def visible_for(self, user):
        if not user.is_authenticated:
            return self.none()

        progreso_lector = ProgresoUsuario.objects.filter(
            usuario=user, obra=OuterRef('obra')
        ).values('orden_absoluto')[:1]

        progreso_cruzado = ProgresoUsuario.objects.filter(
            usuario=user, obra=OuterRef('obra_cruzada')
        ).values('orden_absoluto')[:1]

        return self.annotate(
            progreso_lector=Coalesce(
                Subquery(progreso_lector, output_field=models.IntegerField()),
                Value(0),
            ),
            progreso_cruzado=Coalesce(
                Subquery(progreso_cruzado, output_field=models.IntegerField()),
                Value(0),
            ),
        ).filter(
            Q(author=user)
            | (
                Q(progreso_lector__gte=F('frontera_orden'))
                & (
                    Q(frontera_cruzada_orden__isnull=True)
                    | Q(progreso_cruzado__gte=F('frontera_cruzada_orden'))
                )
            )
        )

    def with_feed_stats(self):
        # Dos Count() sobre relaciones distintas en la misma consulta
        # (reactions, comments) producen un join cruzado: cada fila de
        # reactions se combina con cada fila de comments del mismo post
        # antes de agregar. distinct=True corregia el numero, no el
        # coste -- con posts muy comentados/reaccionados era el
        # principal responsable de la lentitud del feed. Subquery
        # correlacionada por relacion evita el cruce por completo.
        from likes.models import PostReaction
        from comments.models import Comment

        likes_subquery = (
            PostReaction.objects.filter(post=OuterRef('pk'))
            .order_by()
            .values('post')
            .annotate(total=Count('id'))
            .values('total')
        )
        comments_subquery = (
            Comment.objects.filter(post=OuterRef('pk'))
            .order_by()
            .values('post')
            .annotate(total=Count('id'))
            .values('total')
        )

        return self.annotate(
            likes_total=Coalesce(Subquery(likes_subquery, output_field=IntegerField()), Value(0)),
            comments_total=Coalesce(Subquery(comments_subquery, output_field=IntegerField()), Value(0)),
        )