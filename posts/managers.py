from django.db import models
from django.db.models import Count, F, IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from narrative.models import ProgresoUsuario

# Valores de Post.modo_cruce (aquí para no importar el modelo desde el manager).
MODO_CRUCE_COMPARATIVA = 'comparativa'
MODO_CRUCE_MISMA_ESCENA = 'misma_escena'


def progreso_en(user, campo_obra):
    """Progreso del lector en la obra a la que apunta campo_obra; 0 si no ha declarado ninguno."""
    progreso = ProgresoUsuario.objects.filter(
        usuario=user, obra=OuterRef(campo_obra)
    ).values('orden_absoluto')[:1]
    return Coalesce(Subquery(progreso, output_field=IntegerField()), Value(0))


def regla_frontera(progreso, progreso_cruzado, prefijo=''):
    """Regla antispoiler de un post, sin el privilegio del autor.
    prefijo='' desde Post; 'post__' desde Comment para aplicar la de su post.
    Comparativa: ambas fronteras. Misma escena: basta una de las dos."""
    principal = Q(**{f'{progreso}__gte': F(f'{prefijo}frontera_orden')})
    sin_cruce = Q(**{f'{prefijo}frontera_cruzada_orden__isnull': True})
    cruzada = Q(**{f'{progreso_cruzado}__gte': F(f'{prefijo}frontera_cruzada_orden')})
    misma_escena = (
        Q(**{f'{prefijo}modo_cruce': MODO_CRUCE_MISMA_ESCENA}) & ~sin_cruce & (principal | cruzada)
    )
    return (principal & (sin_cruce | cruzada)) | misma_escena


class PostQuerySet(models.QuerySet):
    def visible_for(self, user):
        if not user.is_authenticated:
            return self.none()

        return self.annotate(
            progreso_lector=progreso_en(user, 'obra'),
            progreso_cruzado=progreso_en(user, 'obra_cruzada'),
        ).filter(
            Q(author=user) | regla_frontera('progreso_lector', 'progreso_cruzado')
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