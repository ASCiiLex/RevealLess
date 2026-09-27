import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from unfold.components import BaseComponent, register_component

from comments.models import Comment
from narrative.models import Obra, SolicitudTema
from posts.models import Post

User = get_user_model()

DIAS_VENTANA = 30


def _serie_diaria(queryset, campo_fecha):
    """Cuenta por día de los últimos DIAS_VENTANA días, con 0 en los días
    sin registros (Chart.js necesita el eje X completo, sin huecos)."""
    hoy = timezone.now().date()
    desde = hoy - timedelta(days=DIAS_VENTANA - 1)

    conteos = dict(
        queryset.filter(**{f'{campo_fecha}__date__gte': desde})
        .annotate(dia=TruncDate(campo_fecha))
        .values('dia')
        .annotate(total=Count('id'))
        .values_list('dia', 'total')
    )

    dias = [desde + timedelta(days=i) for i in range(DIAS_VENTANA)]
    etiquetas = [d.strftime('%d/%m') for d in dias]
    valores = [conteos.get(d, 0) for d in dias]
    return etiquetas, valores


@register_component
class ActividadDiariaComponent(BaseComponent):
    """Posts y comentarios creados por día, últimos 30 días."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        etiquetas, posts_serie = _serie_diaria(Post.objects.all(), 'created_at')
        _, comentarios_serie = _serie_diaria(Comment.objects.all(), 'created_at')

        context.update({
            'height': 280,
            'data': json.dumps({
                'labels': etiquetas,
                'datasets': [
                    {'label': 'Posts', 'data': posts_serie},
                    {'label': 'Comentarios', 'data': comentarios_serie},
                ],
            }),
        })
        return context


@register_component
class RegistrosDiariosComponent(BaseComponent):
    """Nuevos usuarios registrados por día, últimos 30 días."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        etiquetas, valores = _serie_diaria(User.objects.all(), 'date_joined')

        context.update({
            'height': 280,
            'data': json.dumps({
                'labels': etiquetas,
                'datasets': [
                    {'label': 'Registros', 'data': valores},
                ],
            }),
        })
        return context


def _actividad_por_obra():
    """% de posts por obra sobre el total, top 6 + 'Otras' agrupadas."""
    total = Post.objects.count()
    if not total:
        return []

    conteos = (
        Obra.objects.annotate(posts_total=Count('posts'))
        .filter(posts_total__gt=0)
        .order_by('-posts_total')
    )

    top = list(conteos[:6])
    resto = sum(o.posts_total for o in conteos[6:])

    items = [
        {
            'title': o.titulo,
            'description': f'{o.posts_total} posts',
            'value': round(o.posts_total / total * 100, 1),
        }
        for o in top
    ]
    if resto:
        items.append({
            'title': 'Otras obras',
            'description': f'{resto} posts',
            'value': round(resto / total * 100, 1),
        })
    return items


def dashboard_callback(request, context):
    """Inyecta las métricas y gráficos que pinta core/templates/admin/index.html."""
    context.update({
        'obras_count': Obra.objects.count(),
        'posts_count': Post.objects.count(),
        'usuarios_count': User.objects.count(),
        'solicitudes_pendientes': SolicitudTema.objects.filter(
            estado=SolicitudTema.ESTADO_PENDIENTE
        ).count(),
        'actividad_por_obra': _actividad_por_obra(),
    })
    return context