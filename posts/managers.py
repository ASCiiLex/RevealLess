from django.db import models
from django.db.models import F, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from narrative.models import ProgresoUsuario


class PostQuerySet(models.QuerySet):
    def visible_for(self, user):
        if not user.is_authenticated:
            return self.none()

        progreso_lector = ProgresoUsuario.objects.filter(
            usuario=user, obra=OuterRef('obra')
        ).values('orden_absoluto')[:1]

        return self.annotate(
            progreso_lector=Coalesce(
                Subquery(progreso_lector, output_field=models.IntegerField()),
                Value(0),
            )
        ).filter(
            Q(author=user) | Q(progreso_lector__gte=F('frontera_orden'))
        )