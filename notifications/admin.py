from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ('id', 'actor', 'user', 'verb', 'target_type', 'target_id', 'reaction', 'created_at', 'seen')
    list_filter = ('seen', 'created_at', 'target_type', 'reaction')
    search_fields = ('actor__username', 'user__username', 'verb')