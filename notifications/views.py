from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Notification

@login_required
def notifications_view(request):

    if request.GET.get("page") in (None, "1"):
        Notification.objects.filter(user=request.user, seen=False).update(seen=True)

    qs = Notification.objects.filter(user=request.user).order_by('-created_at')

    paginator = Paginator(qs, 15)
    page = request.GET.get("page", 1)
    notifications = paginator.get_page(page)

    if request.GET.get("page") and request.GET.get("page") != "1":
        return render(request, "components/notifications/list.html", {
            "notifications": notifications
        })

    return render(request, "notifications/notifications.html", {
        "notifications": notifications
    })

@login_required
def post_not_found_view(request, notif_id):
    notif = Notification.objects.filter(id=notif_id, user=request.user).first()

    return render(request, "notifications/post_not_found.html", {
        "notification": notif
    })


@login_required
def notifications_react_view(request):
    """Vista mínima que monta el punto de entrada de React para
    Notificaciones (Fase 4). No reemplaza notifications_view: convive
    con la vista HTML heredada. El WebSocket de /ws/notifications/ ya
    está registrado en core/routing.py y funciona igual desde React,
    porque la página se sirve desde el mismo origen (Django, puerto
    8000) que el WebSocket -- sin cambios de infraestructura."""
    return render(request, 'notifications/notifications_react.html')