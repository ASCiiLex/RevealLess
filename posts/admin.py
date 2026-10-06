from unfold.admin import ModelAdmin, TabularInline
from django.contrib import admin
from django.db.models import Count
from .models import Hashtag, PersonajeComparado, Post, PostImagen
from comments.models import Comment


class CommentInline(TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('user', 'text', 'created_at')
    # Mismo motivo que en CommentAdmin/PostAdmin: sin esto, el
    # "formulario vacío" oculto de este inline carga un <select> con
    # todo el catálogo de UnidadNarrativa, y eso es lo que ralentizaba
    # /admin/posts/post/add/ aunque el post fuera nuevo y sin comentarios.
    autocomplete_fields = ('referencia_narrativa', 'frontera_spoiler', 'obra_cruzada', 'frontera_cruzada')


class PostImagenInline(TabularInline):
    model = PostImagen
    extra = 0
    fields = ('imagen', 'etiqueta', 'orden')


class PersonajeComparadoInline(TabularInline):
    model = PersonajeComparado
    extra = 0
    raw_id_fields = ('personaje',)


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = (
        'id', 'author', 'obra', 'short_text', 'frontera', 'frontera_origen',
        'created_at', 'likes_count', 'comments_count'
    )
    search_fields = ('author__username', 'text')
    list_filter = ('created_at', 'obra', 'frontera_origen')
    readonly_fields = ('frontera_orden',)
    inlines = [PostImagenInline, PersonajeComparadoInline, CommentInline]
    autocomplete_fields = ('referencia_narrativa', 'frontera_spoiler', 'obra_cruzada', 'frontera_cruzada')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (
            qs.select_related("author", "obra", "frontera_spoiler")
            .prefetch_related("comments")
            .annotate(
                likes_total=Count("reactions", distinct=True),
                comments_total=Count("comments", distinct=True),
            )
        )

    @admin.display(description='Texto')
    def short_text(self, obj):
        return obj.text[:40] + "..." if len(obj.text) > 40 else obj.text

    @admin.display(description='Frontera', ordering='frontera_orden')
    def frontera(self, obj):
        return obj.frontera_spoiler.nombre if obj.frontera_spoiler_id else '-'


@admin.register(Hashtag)
class HashtagAdmin(ModelAdmin):
    """Borrar un hashtag elimina sus vínculos con los posts; el texto de los posts no cambia."""

    list_display = ('name', 'total_posts')
    search_fields = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(num_posts=Count('posts', distinct=True))

    @admin.display(description='Posts', ordering='num_posts')
    def total_posts(self, obj):
        return obj.num_posts