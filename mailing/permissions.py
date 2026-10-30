from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission
from .permissions import is_manager

User = get_user_model()

def is_manager(user: User) -> bool:
    return user.is_authenticated and user.is_staff

class IsManagerPermission(BasePermission):
    message = "Требуется роль менеджера."

    def has_permission(self, request, view):
        return is_manager(request.user)
