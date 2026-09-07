import re
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def send_ws_notification(user, notification):
    channel_layer = get_channel_layer()

    payload = {
        "id": notification.id,
        "actor": notification.actor.username,
        "verb": notification.verb,
        "avatar": notification.avatar,
        "url": notification.url,
        "created_at": notification.created_at.isoformat(),
    }

    async_to_sync(channel_layer.group_send)(
        f"notifications_{user.id}",
        {
            "type": "new_notification",
            "data": payload,
        },
    )


def extract_mentions(text):
    return re.findall(r"@(\w+)", text)


def extract_hashtags(text):
    return re.findall(r"#(\w+)", text)
