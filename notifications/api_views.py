from django.core.paginator import Paginator
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer

PAGE_SIZE = 15


class NotificationListAPIView(APIView):
    """Réplica de notifications_view: mismo comportamiento de marcar
    como vistas las notificaciones no leídas al cargar la primera
    página (o sin parámetro de página), mismo tamaño de página (15)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        page_param = request.query_params.get('page')

        if page_param in (None, '1'):
            Notification.objects.filter(user=request.user, seen=False).update(seen=True)

        qs = Notification.objects.filter(user=request.user).order_by('-created_at')
        paginator = Paginator(qs, PAGE_SIZE)
        page = paginator.get_page(page_param or 1)

        return Response({
            'results': NotificationSerializer(page.object_list, many=True).data,
            'has_next': page.has_next(),
            'page': page.number,
        })