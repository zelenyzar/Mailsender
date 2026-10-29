from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden

def is_manager(user):
    """Проверяет, является ли пользователь менеджером."""
    # Вариант А: Проверка по группе
    return user.groups.filter(name='manager').exists()
    
    # Вариант Б (если нет групп): Проверка по флагу is_staff
    # return user.is_staff 

class OwnerOrManagerMixin:
    """
    Миксин для ListView, DetailView, UpdateView, DeleteView.
    Возвращает queryset:
      - Если пользователь обычный: только его объекты.
      - Если менеджер: все объекты.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        if is_manager(self.request.user):
            return qs
        # Обычные пользователи видят только свои данные
        return qs.filter(owner=self.request.user)

class OwnerCheckMixin:
    """
    Миксин для UpdateView и DeleteView.
    Проверяет, что текущий пользователь является владельцем объекта.
    Менеджеры могут редактировать/удалять всё.
    """
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        
        # Если это менеджер - разрешаем
        if is_manager(request.user):
            return super().dispatch(request, *args, **kwargs)
            
        # Если владелец - разрешаем
        if obj.owner == request.user:
            return super().dispatch(request, *args, **kwargs)
        
        # Иначе - 403 Forbidden
        return HttpResponseForbidden("Вы не можете редактировать чужие данные.")
