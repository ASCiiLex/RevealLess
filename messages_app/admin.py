from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = ('sender', 'receiver', 'text', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'text')
    list_filter = ('created_at',)