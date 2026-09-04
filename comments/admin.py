from django.contrib import admin
from .models import Comment, CommentReaction


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__username', 'text')
    readonly_fields = ('user', 'post', 'parent', 'created_at')


@admin.register(CommentReaction)
class CommentReactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'comment', 'reaction', 'created_at')
    list_filter = ('reaction', 'created_at', 'user')
    search_fields = ('user__username',)
    readonly_fields = ('user', 'comment', 'reaction', 'created_at')