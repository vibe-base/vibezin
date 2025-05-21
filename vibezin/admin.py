from django.contrib import admin
from .models import Vibe, UserProfile, GeneratedImage

# Register your models here.
@admin.register(Vibe)
class VibeAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    list_filter = ('created_at', 'updated_at', 'user')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'created_at', 'updated_at')
    search_fields = ('user__username', 'bio')
    list_filter = ('theme', 'created_at', 'updated_at')

@admin.register(GeneratedImage)
class GeneratedImageAdmin(admin.ModelAdmin):
    list_display = ('user', 'vibe', 'short_prompt', 'model', 'created_at')
    search_fields = ('prompt', 'revised_prompt', 'user__username')
    list_filter = ('model', 'created_at', 'user')

    def short_prompt(self, obj):
        return obj.prompt[:50] + '...' if len(obj.prompt) > 50 else obj.prompt
    short_prompt.short_description = 'Prompt'
