from django.contrib.auth import get_user_model
from narrative.models import Obra, SolicitudTema
from posts.models import Post

User = get_user_model()


def dashboard_callback(request, context):
    """Inyecta las métricas que pinta core/templates/admin/index.html."""
    context.update({
        'obras_count': Obra.objects.count(),
        'posts_count': Post.objects.count(),
        'usuarios_count': User.objects.count(),
        'solicitudes_pendientes': SolicitudTema.objects.filter(
            estado=SolicitudTema.ESTADO_PENDIENTE
        ).count(),
    })
    return context