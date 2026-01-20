# admin.py
from django.contrib import admin
from .models import *

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'username', 'is_online', 'last_seen')
    search_fields = ('phone_number', 'username')
    list_filter = ('is_online', 'theme')

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'chat_type', 'created_at')
    list_filter = ('chat_type',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'chat', 'message_type', 'content', 'created_at')
    list_filter = ('message_type', 'is_deleted')
    search_fields = ('content',)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'only_admins_can_send', 'created_at')
    search_fields = ('name', 'description')

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'status_type', 'created_at', 'expires_at')
    list_filter = ('status_type',)

@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ('caller', 'call_type', 'status', 'started_at', 'duration')
    list_filter = ('call_type', 'status')

@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    search_fields = ('name',)

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'verified', 'created_by', 'created_at')
    list_filter = ('verified',)
    search_fields = ('name',)

@admin.register(AIAssistant)
class AIAssistantAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')