from django.db import models
from django.db.models import Count, F, OuterRef, Q, Subquery, Value
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
        return self.annotate(
            likes_total=Count('reactions', distinct=True),
            comments_total=Count('comments', distinct=True),
        )