from django.contrib import admin
from .models import Vibe, UserProfile

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
