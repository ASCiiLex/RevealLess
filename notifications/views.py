from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def post_not_found_view(request, notif_id):
    notif = Notification.objects.filter(id=notif_id, user=request.user).first()

    return render(request, "notifications/post_not_found.html", {
        "notification": notif
    })


@login_required
def notifications_react_view(request):
    """Monta React para Notificaciones. El WebSocket /ws/notifications/
    (core/routing.py) funciona igual: misma origen."""
    return render(request, 'notifications/notifications_react.html')