from django.db.models import Count, Max, Min, Q
from django.http import Http404
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from subscriptions.models import Suscripcion
from ..models import Categoria, Obra, Personaje, ProgresoUsuario, TemaTransversal
from ..serializers import ObraLandingSerializer, ObraResumenSerializer
from ..services.personajes import (
    identidad_conocida,
    identidades_conocidas,
    ordenar_por_relevancia,
    presentacion_personaje,
    progreso_por_obra,
)
from .comun import contexto_suscripcion_obra, ids_familia, suscripcion_id_por_tema


def _total_suscriptores(**filtro):
    return Suscripcion.objects.filter(**filtro).values('usuario').distinct().count()


def personajes_visibles(obra, progreso):
    """Solo personajes cuya primera aparición en esta obra ya alcanzó el usuario:
    listar uno que aún no ha salido sería en sí mismo un spoiler.
    apariciones_vistas solo cuenta las alcanzadas (el orden lo decide ordenar_por_relevancia)."""
    if not progreso:
        return []
    return list(
        Personaje.objects.filter(unidades__obra=obra)
        .annotate(
            primera_aparicion=Min('unidades__orden_fin', filter=Q(unidades__obra=obra)),
            apariciones_vistas=Count(
                'unidades',
                filter=Q(unidades__obra=obra, unidades__orden_fin__lte=progreso.orden_absoluto),
                distinct=True,
            ),
        )
        .filter(primera_aparicion__lte=progreso.orden_absoluto)
        .prefetch_related('etapas__visible_tras')
        .distinct()
    )


def obras_visibles_de_personaje(personaje, usuario):
    """Obras donde el usuario ya alcanzó la primera aparición del personaje.
    Las demás no se listan: saber que aparece ahí ya es un spoiler."""
    progreso = progreso_por_obra(usuario)
    primeras = personaje.unidades.order_by().values('obra_id').annotate(primera=Min('orden_fin'))
    ids = [
        fila['obra_id']
        for fila in primeras
        if fila['primera'] is not None
        and fila['obra_id'] in progreso
        and progreso[fila['obra_id']] >= fila['primera']
    ]
    return Obra.objects.filter(id__in=ids).order_by('titulo')


def _suscripcion_id_por_personaje(usuario):
    return dict(
        Suscripcion.objects.filter(usuario=usuario, personaje__isnull=False)
        .values_list('personaje_id', 'id')
    )


def _identidad(personaje, progreso):
    return {'id': personaje.id, 'nombre': presentacion_personaje(personaje, progreso)['nombre']}


class ObraLandingAPIView(APIView):
    """Sinopsis, categorías, progreso, suscriptores, temas, obras relacionadas y personajes ya conocidos."""

    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(
            Obra.objects.prefetch_related('categorias').annotate(longitud_total=Max('unidades__orden_fin')),
            slug=obra_slug,
        )
        progreso = ProgresoUsuario.objects.filter(usuario=request.user, obra=obra).first()

        contexto = {
            **contexto_suscripcion_obra(request.user),
            'progreso': progreso,
            'longitud_total': obra.longitud_total,
            'total_suscriptores': _total_suscriptores(obra=obra),
            'suscripcion_id_por_tema': suscripcion_id_por_tema(request.user),
            'personajes_visibles': ordenar_por_relevancia(
                personajes_visibles(obra, progreso), obra, request.user,
            ),
            'suscripcion_id_por_personaje': _suscripcion_id_por_personaje(request.user),
            'progreso_por_obra': progreso_por_obra(request.user),
        }

        return Response(ObraLandingSerializer(obra, context=contexto).data)


class TemaLandingAPIView(APIView):
    """Agrupa por nombre los temas de la misma franquicia en tiempo de consulta.
    'Seguir' actúa siempre sobre el TemaTransversal concreto de la URL."""

    permission_classes = [IsAuthenticated]

    def get(self, request, tema_id):
        tema = get_object_or_404(TemaTransversal.objects.select_related('obra'), id=tema_id)
        temas_grupo = list(
            TemaTransversal.objects
            .filter(nombre=tema.nombre, obra_id__in=ids_familia(tema.obra))
            .select_related('obra')
        )

        suscripcion = Suscripcion.objects.filter(usuario=request.user, tema__in=temas_grupo).first()

        return Response({
            'id': tema.id,
            'nombre': tema.nombre,
            'obra_slug': tema.obra.slug,
            'obras': [
                {'id': t.obra.id, 'titulo': t.obra.titulo, 'slug': t.obra.slug, 'tema_id': t.id}
                for t in temas_grupo
            ],
            'suscrito': suscripcion is not None,
            'suscripcion_id': suscripcion.id if suscripcion else None,
            'total_suscriptores': _total_suscriptores(tema__in=temas_grupo),
        })


class CategoriaLandingAPIView(APIView):
    """Obras de una categoría con el mismo formato que los lomos del carrusel."""

    permission_classes = [IsAuthenticated]

    def get(self, request, categoria_id):
        categoria = get_object_or_404(Categoria, id=categoria_id)
        obras = (
            categoria.obras.prefetch_related('categorias')
            .annotate(longitud_total=Max('unidades__orden_fin'))
            .order_by('titulo')
        )
        contexto = {
            'progreso_por_obra': progreso_por_obra(request.user),
            **contexto_suscripcion_obra(request.user),
        }
        datos = ObraResumenSerializer(obras, many=True, context=contexto).data

        return Response({
            'id': categoria.id,
            'nombre': categoria.nombre,
            'total_obras': len(datos),
            'obras': datos,
        })


class PersonajeLandingAPIView(APIView):
    """Landing de personaje filtrada por progreso. Sin ninguna aparición alcanzada
    responde 404, igual que si no existiera: la URL directa no debe revelarlo.
    Nombre, imagen y nota salen de la etapa más reciente ya superada. Con ?obra=<slug>
    (desde el carrusel) solo cuentan las etapas de esa obra, si ya se alcanzó en ella;
    si no, se ignora y se usan todas las obras alcanzadas.
    Las identidades vinculadas (Sogeking ↔ Usopp) solo aparecen si el lector ya conoce el vínculo."""

    permission_classes = [IsAuthenticated]

    def get(self, request, personaje_id):
        personaje = get_object_or_404(
            Personaje.objects.select_related('identidad_de').prefetch_related(
                'etapas__visible_tras', 'identidad_revelada_tras', 'identidad_de__etapas__visible_tras',
            ),
            id=personaje_id,
        )
        obras = list(obras_visibles_de_personaje(personaje, request.user))
        if not obras:
            raise Http404

        progreso = progreso_por_obra(request.user)
        slug = request.query_params.get('obra')
        obra_contexto = next((o for o in obras if o.slug == slug), None)
        presentacion = presentacion_personaje(
            personaje, progreso, obra_id=obra_contexto.id if obra_contexto else None,
        )
        suscripcion = Suscripcion.objects.filter(usuario=request.user, personaje=personaje).first()

        identidad_de = None
        if personaje.identidad_de_id and identidad_conocida(personaje, progreso):
            identidad_de = _identidad(personaje.identidad_de, progreso)

        return Response({
            'id': personaje.id,
            **presentacion,
            'contexto': {'titulo': obra_contexto.titulo, 'slug': obra_contexto.slug} if obra_contexto else None,
            'identidad_de': identidad_de,
            'otras_identidades': [_identidad(a, progreso) for a in identidades_conocidas(personaje, progreso)],
            'obras': [
                {'id': o.id, 'titulo': o.titulo, 'slug': o.slug, 'imagen_url': o.image_url}
                for o in obras
            ],
            'suscripcion_id': suscripcion.id if suscripcion else None,
            'total_suscriptores': _total_suscriptores(personaje=personaje),
        })