from .models import Message

def unread_messages(request):
    if not request.user.is_authenticated:
        return {"unread_messages_count": 0}

    count = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    return {"unread_messages_count": count}