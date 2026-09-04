from django.contrib import admin
from .models import PostReaction


@admin.register(PostReaction)
class PostReactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'reaction', 'created_at')
    search_fields = ('user__username', 'post__id')
    list_filter = ('reaction', 'created_at', 'user')
    readonly_fields = ('user', 'post', 'reaction', 'created_at')