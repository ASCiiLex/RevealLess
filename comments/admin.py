from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import Comment, CommentReaction


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ('id', 'user', 'post', 'frontera_origen', 'created_at')
    list_filter = ('created_at', 'user', 'frontera_origen')
    search_fields = ('user__username', 'text')
    readonly_fields = ('user', 'post', 'parent', 'created_at', 'frontera_orden')
    # Mismo motivo que en PostAdmin: evita el <select> de 1000+ opciones.
    autocomplete_fields = ('referencia_narrativa', 'frontera_spoiler', 'obra_cruzada', 'frontera_cruzada')

    def get_queryset(self, request):
        # Sin esto, 'post' en list_display dispara una query por fila
        # (N+1) -- 'user' también se muestra, así que entra en el mismo
        # select_related.
        return super().get_queryset(request).select_related('user', 'post')


@admin.register(CommentReaction)
class CommentReactionAdmin(ModelAdmin):
    list_display = ('id', 'user', 'comment', 'reaction', 'created_at')
    list_filter = ('reaction', 'created_at', 'user')
    search_fields = ('user__username',)
    readonly_fields = ('user', 'comment', 'reaction', 'created_at')