# mailing/permissions.py
from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission

User = get_user_model()

def is_manager(user: User) -> bool:
    return bool(user and user.is_authenticated and user.is_staff)


class IsManagerPermission(BasePermission):
    message = "Требуется роль менеджера."

    def has_permission(self, request, view):
        return is_manager(request.user)
