from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display  = ['sender', 'group', 'content', 'is_edited', 'created_at']
    list_filter   = ['group', 'is_edited']
    search_fields = ['sender__email', 'group__name', 'content']
    readonly_fields = ['created_at', 'updated_at']
