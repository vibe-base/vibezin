from django.contrib import admin
from .models import Vibe

# Register your models here.
@admin.register(Vibe)
class VibeAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    list_filter = ('created_at', 'updated_at')
