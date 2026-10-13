from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Coalesce
from narrative.models import ClasificacionNarrativa
from posts.managers import progreso_en, regla_frontera
from posts.models import Post


class CommentQuerySet(models.QuerySet):
    def visible_for(self, user):
        if not user.is_authenticated:
            return self.none()

        heredado = Q(frontera_origen=ClasificacionNarrativa.ORIGEN_HEREDADO_POST)
        # Heredado: la regla de su post (incluida «misma escena»), sin el privilegio de su autor.
        regla_heredada = heredado & regla_frontera('progreso_lector', 'progreso_post_cruzado', prefijo='post__')
        regla_propia = ~heredado & Q(progreso_lector__gte=F('frontera_efectiva_calculada'))
        cruce_propio = (
            Q(frontera_cruzada_orden__isnull=True)
            | Q(progreso_cruzado__gte=F('frontera_cruzada_orden'))
        )

        return self.annotate(
            frontera_efectiva_calculada=Coalesce('frontera_orden', 'post__frontera_orden'),
            progreso_lector=progreso_en(user, 'post__obra'),
            progreso_post_cruzado=progreso_en(user, 'post__obra_cruzada'),
            progreso_cruzado=progreso_en(user, 'obra_cruzada'),
        ).filter(
            post__in=Post.objects.visible_for(user),
        ).filter(
            Q(user=user) | ((regla_heredada | regla_propia) & cruce_propio)
        )