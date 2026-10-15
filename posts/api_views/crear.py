from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from narrative.ai_assistant import proponer_clasificacion
from narrative.models import Obra, ProgresoUsuario, ClasificacionNarrativa
from narrative.serializers import PostSerializer
from narrative.services import (
    actualizar_progreso,
    SaltoGrandeRequiereConfirmacion,
    detectar_posibles_referencias_cruzadas,
    proponer_tema,
)
from narrative.services.detecciones import serializar_detecciones
from narrative.services.etiquetado import etiquetar_personajes
from narrative.services.personajes import proponer_personaje
from ..models import PersonajeComparado, Post, PostImagen, misma_historia
from ..serializers import PostCreateSerializer
from .comun import (
    ERROR_COMPARADO_AJENO,
    ERROR_CRUZADA_INCOMPLETA,
    ERROR_DISPOSICION,
    ERROR_IMAGEN_Y_GALERIA,
    ERROR_MODO_CRUCE,
    ERROR_NUMERO_COMPARADOS,
    ERROR_SIN_REFERENCIA,
    ERROR_TEMA_OTRA_OBRA,
    error_400,
    tema_de_otra_obra,
)


def _id_entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _confianza(valor):
    try:
        return max(0.0, min(1.0, float(valor)))
    except (TypeError, ValueError):
        return None


def _asignar_frontera(post, obra, progreso, frontera_explicita, sugerida_id=None, confianza=None):
    """Prioridad: elegida por el autor (origen IA si acepta tal cual la propuesta previa)
    > propuesta IA al publicar > fallback al progreso actual."""
    if frontera_explicita:
        post.frontera_spoiler = frontera_explicita
        if sugerida_id == frontera_explicita.id:
            post.frontera_origen = ClasificacionNarrativa.ORIGEN_IA
            post.ia_confianza = confianza
            post.clasificado_en = timezone.now()
        else:
            post.frontera_origen = ClasificacionNarrativa.ORIGEN_EXPLICITO
        return

    sugerencia = proponer_clasificacion(post.text, obra, post.referencia_narrativa)
    if sugerencia.es_utilizable:
        post.frontera_spoiler = sugerencia.frontera_spoiler
        post.frontera_origen = ClasificacionNarrativa.ORIGEN_IA
        post.ia_confianza = sugerencia.confianza
        post.clasificado_en = timezone.now()
    else:
        post.frontera_spoiler = progreso.unidad_actual
        post.frontera_origen = ClasificacionNarrativa.ORIGEN_FALLBACK


def _cubrir_personajes_comparados(post, comparados):
    """Eleva la frontera (o la cruzada) hasta la primera aparición de cada personaje
    comparado: quien pueda leer el post ya los conoce a todos."""
    for personaje in comparados:
        for obra_id, campo in ((post.obra_id, 'frontera_spoiler'), (post.obra_cruzada_id, 'frontera_cruzada')):
            if not obra_id:
                continue
            primera = personaje.unidades.filter(obra_id=obra_id).order_by('orden_fin').first()
            if primera is None:
                continue
            actual = getattr(post, campo)
            if actual is None or primera.orden_fin > actual.orden_fin:
                setattr(post, campo, primera)
            break


def _nombres_limpios(nombres):
    vistos, limpios = set(), []
    for nombre in nombres:
        nombre = ' '.join(nombre.split())[:150]
        if nombre and nombre.lower() not in vistos:
            vistos.add(nombre.lower())
            limpios.append(nombre)
    return limpios


def _en(lista, indice, defecto):
    return lista[indice] if indice < len(lista) else defecto


class PostCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        progreso = ProgresoUsuario.objects.filter(usuario=request.user, obra=obra).first()
        if not progreso:
            return Response(
                {'detail': 'progreso_requerido', 'obra_slug': obra.slug},
                status=status.HTTP_409_CONFLICT,
            )

        entrada = PostCreateSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data

        obra_cruzada = datos.get('obra_cruzada')
        frontera_cruzada = datos.get('frontera_cruzada')
        if bool(obra_cruzada) != bool(frontera_cruzada):
            return error_400(ERROR_CRUZADA_INCOMPLETA)
        modo_cruce = datos.get('modo_cruce') or Post.MODO_COMPARATIVA
        if not obra_cruzada:
            modo_cruce = Post.MODO_COMPARATIVA
        elif modo_cruce == Post.MODO_MISMA_ESCENA and not misma_historia(obra, obra_cruzada):
            return error_400(ERROR_MODO_CRUCE)

        tema = datos.get('tema')
        if tema_de_otra_obra(tema, obra.id):
            return error_400(ERROR_TEMA_OTRA_OBRA)
        tema_propuesto = (datos.get('tema_propuesto') or '').strip()
        referencia = datos.get('referencia_narrativa')
        frontera_explicita = datos.get('frontera_spoiler')
        # La parte es contexto; la visibilidad la decide la frontera. Con solo frontera, el post va sin parte.
        if not (referencia or tema or tema_propuesto or frontera_explicita):
            return error_400(ERROR_SIN_REFERENCIA)

        imagen_unica = datos.get('image')
        imagenes = list(datos.get('imagenes') or [])
        if imagen_unica and imagenes:
            return error_400(ERROR_IMAGEN_Y_GALERIA)
        if len(imagenes) == 1:
            imagen_unica, imagenes = imagenes[0], []
        disposicion = datos.get('disposicion') or Post.DISPOSICION_AUTO
        if not imagenes:
            disposicion = Post.DISPOSICION_AUTO
        elif disposicion and disposicion not in Post.DISPOSICIONES_POR_NUMERO[len(imagenes)]:
            return error_400(ERROR_DISPOSICION)
        etiquetas = list(datos.get('etiquetas') or [])
        enfoques_x = list(datos.get('enfoques_x') or [])
        enfoques_y = list(datos.get('enfoques_y') or [])
        zooms = list(datos.get('zooms') or [])

        comparados = list(dict.fromkeys(datos.get('personajes_comparados') or []))
        propuestos = _nombres_limpios(datos.get('personajes_propuestos') or [])
        total_comparados = len(comparados) + len(propuestos)
        if total_comparados and not Post.MIN_COMPARADOS <= total_comparados <= Post.MAX_COMPARADOS:
            return error_400(ERROR_NUMERO_COMPARADOS)
        if comparados:
            obras_validas = [obra.id] + ([obra_cruzada.id] if obra_cruzada else [])
            if any(not p.unidades.filter(obra_id__in=obras_validas).exists() for p in comparados):
                return error_400(ERROR_COMPARADO_AJENO)

        if not obra_cruzada and not datos.get('descartar_referencia_cruzada'):
            detecciones = detectar_posibles_referencias_cruzadas(datos['text'], obra)
            if detecciones:
                return Response({
                    'detail': 'referencia_cruzada_detectada',
                    'detecciones': serializar_detecciones(detecciones, obra),
                }, status=status.HTTP_409_CONFLICT)

        # El progreso solo se actualiza tras superar todas las validaciones previas.
        nuevo_progreso = datos.get('nuevo_progreso')
        if nuevo_progreso:
            try:
                progreso = actualizar_progreso(
                    request.user, obra, nuevo_progreso,
                    confirmado=datos.get('confirmar_salto_progreso', False),
                )
            except SaltoGrandeRequiereConfirmacion as exc:
                return Response({
                    'detail': str(exc),
                    'requiere_confirmacion_progreso': True,
                    'salto': exc.salto,
                }, status=status.HTTP_409_CONFLICT)
            except ValueError as exc:
                return error_400({'nuevo_progreso': [str(exc)]})

        post = Post(
            author=request.user,
            obra=obra,
            text=datos['text'],
            image=imagen_unica,
            disposicion=disposicion,
            referencia_narrativa=referencia,
            nivel_spoiler=datos.get('nivel_spoiler', ClasificacionNarrativa.NIVEL_MENOR),
            emocion_autor=datos.get('emocion_autor'),
            obra_cruzada=obra_cruzada,
            frontera_cruzada=frontera_cruzada,
            modo_cruce=modo_cruce,
        )
        # frontera_sugerida_ia: la propuesta vista antes de publicar; si coincide con la elegida, origen IA.
        _asignar_frontera(
            post, obra, progreso, frontera_explicita,
            _id_entero(request.data.get('frontera_sugerida_ia')),
            _confianza(request.data.get('ia_confianza')),
        )
        _cubrir_personajes_comparados(post, comparados)

        galeria = [
            PostImagen(
                imagen=archivo,
                etiqueta=_en(etiquetas, i, '').strip(),
                orden=i,
                enfoque_x=_en(enfoques_x, i, PostImagen.ENFOQUE_CENTRO),
                enfoque_y=_en(enfoques_y, i, PostImagen.ENFOQUE_CENTRO),
                zoom=_en(zooms, i, PostImagen.ZOOM_BASE),
            )
            for i, archivo in enumerate(imagenes)
        ]
        try:
            post.full_clean()
            for imagen in galeria:
                imagen.full_clean(exclude=['post'])
        except ValidationError as exc:
            return error_400(exc.message_dict)

        with transaction.atomic():
            post.save()
            for imagen in galeria:
                imagen.post = post
                imagen.save()
            filas = [PersonajeComparado(post=post, personaje=p, orden=i) for i, p in enumerate(comparados)]
            # Propuestos: aparición provisional en la frontera del post; el admin la ajusta al aprobar.
            for i, nombre in enumerate(propuestos, start=len(comparados)):
                solicitud = proponer_personaje(obra, post.frontera_spoiler, request.user, nombre)
                filas.append(PersonajeComparado(post=post, solicitud=solicitud, orden=i))
            PersonajeComparado.objects.bulk_create(filas)

        # Solo tras publicar: un post rechazado no deja solicitudes de tema sueltas.
        if not tema and tema_propuesto:
            tema = proponer_tema(obra, request.user, tema_propuesto)
        if tema:
            post.temas_transversales.set([tema])
        # Tras guardar: necesita frontera_orden ya calculado.
        etiquetar_personajes(post)

        return Response(
            PostSerializer(post, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )