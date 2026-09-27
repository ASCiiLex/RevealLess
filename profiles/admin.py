from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import Profile
from django.utils.html import format_html

@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    list_display = ('user', 'bio_short', 'interests', 'image_tag')
    search_fields = ('user__username', 'interests')
    list_filter = ('interests',)

    def bio_short(self, obj):
        return obj.bio[:40] + "..." if len(obj.bio) > 40 else obj.bio
    bio_short.short_description = "Bio"

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="40" height="40" style="border-radius:50%"/>', obj.image.url)
        return "-"
    image_tag.short_description = "Foto"