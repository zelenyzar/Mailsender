from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Объект доступен, только если его создатель — текущий пользователь."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
