from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated

from posts.models import Post
from subscriptions.models import Suscripcion
from subscriptions.services import (
    filtro_posts_silenciados,
    filtro_posts_suscripciones,
    q_posts_de_personaje,
    q_posts_de_unidad,
)
from ..models import Obra, TemaTransversal, UnidadNarrativa
from ..serializers import PostSerializer
from ..services.personajes import ids_con_identidades
from .comun import entero_o_none, ids_familia

VISTA_BIBLIOTECA = 'biblioteca'
VISTA_DESCUBRIR = 'descubrir'
VISTAS = (VISTA_BIBLIOTECA, VISTA_DESCUBRIR)


class FeedCursorPagination(CursorPagination):
    """Cursor y no offset: los posts nuevos no desplazan las páginas ya cargadas
    y se evita el COUNT sobre visible_for()."""

    page_size = 12
    ordering = ('-created_at', '-id')


def q_biblioteca(user):
    """Lo que llega por Biblioteca: propios, seguidos, suscripciones activas y comparativas
    que cruzan una obra seguida. Única definición: Descubrir es su complemento."""
    obras_seguidas = Suscripcion.objects.filter(
        usuario=user, activa=True, obra__isnull=False, unidad__isnull=True, tema__isnull=True,
    ).values('obra_id')

    return (
        Q(author=user)
        | Q(author__in=user.following.values_list('followed', flat=True))
        | filtro_posts_suscripciones(user)
        | Q(obra_cruzada_id__in=obras_seguidas)
    )


class FeedAPIView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = FeedCursorPagination

    def get_serializer_context(self):
        return {'request': self.request}

    def list(self, request, *args, **kwargs):
        respuesta = super().list(request, *args, **kwargs)
        respuesta.data['obra_filtro'] = self._obra_filtro(request.query_params)
        return respuesta

    def _obra_filtro(self, params):
        """Título y slug de la obra filtrada para la cabecera: el primer post no sirve
        (sin posts no hay título y en una comparativa puede ser la otra obra)."""
        obra_id = entero_o_none(params.get('obra'), 'obra')
        if obra_id is None:
            return None
        return Obra.objects.filter(id=obra_id).values('titulo', 'slug').first()

    def _vista(self, params):
        vista = params.get('vista') or VISTA_BIBLIOTECA
        if vista not in VISTAS:
            raise ValidationError({'vista': [f'Debe ser una de: {", ".join(VISTAS)}.']})
        return vista

    def _ids_del_feed(self, user, params):
        """Qué posts entran en el feed, solo como ids. Los joins de las condiciones pueden repetir
        un post; el IN de la consulta principal los descarta sin DISTINCT sobre filas anchas."""
        biblioteca = Post.objects.filter(q_biblioteca(user))
        if self._vista(params) == VISTA_DESCUBRIR:
            # Contenido ajeno que no llega por ninguna otra vía; visible_for decide qué se lee.
            base = Post.objects.exclude(id__in=biblioteca.values('id'))
        else:
            base = biblioteca
        base = base.exclude(filtro_posts_silenciados(user))

        obra_id = entero_o_none(params.get('obra'), 'obra')
        if obra_id is not None:
            base = base.filter(Q(obra_id=obra_id) | Q(obra_cruzada_id=obra_id))

        hashtag = params.get('hashtag')
        if hashtag is not None:
            base = base.filter(post_hashtags__hashtag__name=hashtag)

        tema_id = entero_o_none(params.get('tema'), 'tema')
        if tema_id is not None:
            tema = get_object_or_404(TemaTransversal.objects.select_related('obra'), id=tema_id)
            base = base.filter(
                temas_transversales__nombre=tema.nombre,
                temas_transversales__obra_id__in=ids_familia(tema.obra),
            )

        personaje_id = entero_o_none(params.get('personaje'), 'personaje')
        if personaje_id is not None:
            # Incluye sus otras identidades ya conocidas por el lector (Usopp → también Sogeking).
            base = base.filter(q_posts_de_personaje(ids_con_identidades(personaje_id, user)))

        unidad_id = entero_o_none(params.get('unidad'), 'unidad')
        if unidad_id is not None:
            # Mismo alcance que la suscripción a una unidad; visible_for sigue decidiendo qué se lee.
            base = base.filter(q_posts_de_unidad(get_object_or_404(UnidadNarrativa, id=unidad_id)))

        return base.values('id')

    def get_queryset(self):
        user = self.request.user
        return (
            Post.objects
            .filter(id__in=self._ids_del_feed(user, self.request.query_params))
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
                'imagenes',
                'temas_transversales',
                'comparaciones__personaje__etapas__visible_tras',
                'comparaciones__solicitud',
            )
            .visible_for(user)
            .with_feed_stats()
            .order_by('-created_at', '-id')
        )