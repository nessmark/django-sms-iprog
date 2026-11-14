from django.contrib import admin
from .models import SMSMessage, Contact, QuickTemplate


@admin.register(SMSMessage)
class SMSMessageAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'status', 'gateway_message_id', 'character_count', 'segment_count', 'is_simulation', 'created_at')
    list_filter = ('status', 'is_simulation', 'created_at')
    search_fields = ('phone_number', 'message', 'gateway_message_id')
    readonly_fields = ('created_at', 'gateway_response')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'email', 'created_at')
    search_fields = ('name', 'phone_number', 'email')


@admin.register(QuickTemplate)
class QuickTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    search_fields = ('title', 'content')
