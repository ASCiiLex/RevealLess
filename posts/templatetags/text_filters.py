import re
from django import template
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def urlize_mentions(text):
    text = escape(text)

    def replace(match):
        username = match.group(1)
        url = reverse('profile', args=[username])
        return f'<a href="{url}">@{username}</a>'

    return mark_safe(re.sub(r'@(\w+)', replace, text))


@register.filter
def urlize_hashtags(text):
    text = escape(text)

    def replace(match):
        tag = match.group(1).lower().strip()
        tag = re.sub(r'[^\w]', '', tag)
        url = reverse('hashtag_detail', args=[tag])
        return f'<a href="{url}">#{tag}</a>'

    return mark_safe(re.sub(r'#(\w+)', replace, text))