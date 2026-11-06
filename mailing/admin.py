from django.contrib import admin

from .models import Client, Message, Mailing, MailingAttempt


class OwnerFilterAdmin(admin.ModelAdmin):
    """Базовый админ-класс: менеджер видит только свои записи,
    удалять чужие может только суперпользователь."""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Client)
class ClientAdmin(OwnerFilterAdmin):
    list_display = ('email', 'full_name', 'owner_display')
    search_fields = ('email', 'full_name')

    def owner_display(self, obj):
        return obj.owner.email if obj.owner else 'Нет владельца'

    owner_display.short_description = 'Владелец'

    def save_model(self, request, obj, form, change):
        """
        Автоматически назначает владельца при создании новой записи.
        При редактировании (change=True) владельца не меняет.
        """
        if not change:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


@admin.register(Message)
class MessageAdmin(OwnerFilterAdmin):
    list_display = ('subject', 'owner_display')
    search_fields = ('subject',)

    def owner_display(self, obj):
        return obj.owner.email if obj.owner else 'Нет владельца'

    owner_display.short_description = 'Владелец'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


@admin.register(Mailing)
class MailingAdmin(OwnerFilterAdmin):
    list_display = ('pk', 'status', 'start_time', 'end_time', 'owner_display')
    list_filter = ('status',)
    readonly_fields = ('status',)

    def owner_display(self, obj):
        return obj.owner.email if obj.owner else 'Нет владельца'

    owner_display.short_description = 'Владелец'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


@admin.register(MailingAttempt)
class MailingAttemptAdmin(OwnerFilterAdmin):
    list_display = ('mailing', 'client', 'status', 'sent_at', 'owner_display')
    list_filter = ('status', 'mailing')
    search_fields = ('client__email', 'error_message')
    readonly_fields = ('sent_at',)
    date_hierarchy = 'sent_at'

    def owner_display(self, obj):
        return obj.owner.email if obj.owner else '-'

    owner_display.short_description = 'Владелец'

    def save_model(self, request, obj, form, change):
        if not change and not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)
