from django.contrib import admin
from .models import Client, Message, Mailing, MailingAttempt

@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ('mailing', 'client', 'status', 'sent_at')
    list_filter = ('status', 'mailing')
    search_fields = ('client__email', 'error_message')
    readonly_fields = ('sent_at',)
    date_hierarchy = 'sent_at'
