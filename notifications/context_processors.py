from notifications.models import Notification

def unread_notifications(request):
    if request.user.is_authenticated:
        return {
            "unread_notifications_count": Notification.objects.filter(
                user=request.user,
                seen=False
            ).count()
        }
    return {"unread_notifications_count": 0}