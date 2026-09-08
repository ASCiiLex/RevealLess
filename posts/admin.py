from django.contrib import admin
from django.db.models import Count
from .models import Post
from comments.models import Comment


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('user', 'text', 'created_at')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'author', 'obra', 'short_text', 'frontera_origen',
        'created_at', 'likes_count', 'comments_count'
    )
    search_fields = ('author__username', 'text')
    list_filter = ('created_at', 'obra', 'frontera_origen')
    readonly_fields = ('frontera_orden',)
    inlines = [CommentInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (
            qs.select_related("author", "obra")
            .prefetch_related("comments")
            .annotate(
                likes_total=Count("reactions", distinct=True),
                comments_total=Count("comments", distinct=True),
            )
        )

    def short_text(self, obj):
        return obj.text[:40] + "..." if len(obj.text) > 40 else obj.text
    short_text.short_description = "Texto"