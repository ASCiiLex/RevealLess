import re
from django import template
from django.urls import reverse

register = template.Library()


@register.filter
def urlize_mentions(text):
    def replace(match):
        username = match.group(1)
        url = reverse('profile', args=[username])
        return f'<a href="{url}">@{username}</a>'

    return re.sub(r'@(\w+)', replace, text)


@register.filter
def urlize_hashtags(text):
    def replace(match):
        tag = match.group(1).lower().strip()

        # 🔥 limpiar caracteres raros al final
        tag = re.sub(r'[^\w]', '', tag)

        url = reverse('hashtag_detail', args=[tag])

        return f'<a href="{url}">#{tag}</a>'

    return re.sub(r'#(\w+)', replace, text)