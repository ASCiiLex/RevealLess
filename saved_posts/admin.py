from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import SavedPost


@admin.register(SavedPost)
class SavedPostAdmin(ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('user__username', 'post__id')
    list_filter = ('created_at',)