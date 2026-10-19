from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from narrative.models import ClasificacionNarrativa
from narrative.services import detectar_posibles_referencias_cruzadas
from narrative.services.detecciones import serializar_detecciones
from posts.models import Post
from ..models import Comment
from ..serializers import CommentCreateSerializer
from .fronteras import ajustar_frontera
from .respuestas import datos_clasificacion


def _error(mensaje, status=400):
    return JsonResponse({'error': mensaje}, status=status)


@login_required
@require_POST
def add_comment(request):
    post_id = request.POST.get('post_id', '')
    if not post_id.isdigit():
        return _error('post_id no válido')

    entrada = CommentCreateSerializer(data=request.POST)
    if not entrada.is_valid():
        primer_error = next(iter(entrada.errors.values()))[0]
        return _error(str(primer_error))

    datos = entrada.validated_data
    text = datos['text'].strip()
    if not text:
        return _error('Texto vacío')

    # Solo se comenta (o responde) sobre contenido visible para el usuario.
    post = get_object_or_404(Post.objects.visible_for(request.user), id=post_id)

    parent = None
    parent_id = datos.get('parent_id')
    if parent_id:
        parent = get_object_or_404(
            Comment.objects.visible_for(request.user), id=parent_id, post=post
        )
        # Máximo 3 niveles: si el padre ya tiene abuelo, sería un 4º nivel.
        if parent.parent_id and parent.parent.parent_id:
            return _error('No se puede responder más allá de una respuesta anidada.')

    obra_cruzada = datos.get('obra_cruzada')
    frontera_cruzada = datos.get('frontera_cruzada')
    if bool(obra_cruzada) != bool(frontera_cruzada):
        return _error('Indica la obra cruzada y su frontera juntas, o ninguna de las dos.')

    if not obra_cruzada and not datos.get('descartar_referencia_cruzada'):
        detecciones = detectar_posibles_referencias_cruzadas(text, post.obra)
        if detecciones:
            return JsonResponse({
                'detail': 'referencia_cruzada_detectada',
                'detecciones': serializar_detecciones(detecciones),
            }, status=409)

    comment = Comment(
        user=request.user, post=post, parent=parent, text=text,
        # Un post solo de tema no tiene parte: se usa su frontera, que siempre existe.
        referencia_narrativa=(
            datos.get('referencia_narrativa') or post.referencia_narrativa or post.frontera_spoiler
        ),
        emocion_autor=datos.get('emocion_autor'),
        obra_cruzada=obra_cruzada,
        frontera_cruzada=frontera_cruzada,
    )

    frontera = datos.get('frontera_spoiler')
    if frontera:
        comment.frontera_spoiler = frontera
        comment.frontera_origen = ClasificacionNarrativa.ORIGEN_EXPLICITO
    ajustar_frontera(comment)

    try:
        comment.full_clean()
    except ValidationError as exc:
        return JsonResponse({'error': exc.message_dict}, status=400)

    # Las notificaciones (comentario, respuesta, menciones) las crea Comment.save().
    comment.save()

    return JsonResponse({
        'id': comment.id,
        'user': comment.user.username,
        'text': comment.text,
        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
        'parent_id': comment.parent_id,
        **datos_clasificacion(comment),
        'likes_count': 0,
    })