import re
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def send_ws_notification(user, data):
    channel_layer = get_channel_layer()

    # 🔥 soporta dict o instancia
    if hasattr(data, "actor"):
        payload = {
            "actor": data.actor.username,
            "verb": data.verb,
            "avatar": data.avatar,
            "url": data.url,
            "created_at": data.created_at.isoformat(),
        }
    else:
        payload = {
            "actor": data.get("actor"),
            "verb": data.get("verb"),
            "avatar": data.get("avatar", "/static/img/default_profile.jpg"),
            "url": data.get("url", "#"),
            "created_at": data.get("created_at"),
        }

    async_to_sync(channel_layer.group_send)(
        f"notifications_{user.id}",
        {
            "type": "new_notification",
            "data": payload,
        },
    )


def extract_mentions(text):
    return re.findall(r'@(\w+)', text)


def extract_hashtags(text):
    return re.findall(r'#(\w+)', text)