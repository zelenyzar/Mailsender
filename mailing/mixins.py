# mailing/mixins.py
from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

def is_manager(user: User) -> bool:
    """
    Чётко фиксирует, кто считается менеджером.
    
    Приоритет:
    1. Если пользователь в группе 'manager' → менеджер.
    2. Если нет группы, но стоит флаг is_staff → менеджер (fallback).
    3. Иначе — не менеджер.
    
    Важно: сначала проверяем группы, чтобы при масштабировании
    можно было гибко управлять ролями без изменения кода.
    """
    if not user or not user.is_authenticated:
        return False

    # Вариант А: проверка по группе (рекомендуется)
    if user.groups.filter(name='manager').exists():
        return True

    # Вариант Б: fallback на is_staff (если группы ещё не настроены)
    return user.is_staff


class OwnerOrManagerMixin:
    """
    Миксин для ListView, DetailView и т.п.
    Возвращает queryset:
      - Если пользователь обычный: только его объекты (owner == user).
      - Если менеджер: все объекты.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if is_manager(user):
            # Менеджер видит всё
            return qs

        # Обычный пользователь видит только свои объекты
        # Важно: если у модели нет поля owner, этот фильтр вызовет ошибку —
        # убедись, что у всех моделей, использующих этот миксин, есть поле owner.
        return qs.filter(owner=user)


class OwnerCheckMixin:
    """
    Миксин для UpdateView и DeleteView.
    Проверяет, что текущий пользователь:
      - либо владелец объекта,
      - либо менеджер.
    Иначе возвращает 403 Forbidden.
    """
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        
        # Сначала получаем объект (может выбросить 404 — это нормально)
        obj = self.get_object()

        # Если менеджер — разрешаем всё
        if is_manager(user):
            return super().dispatch(request, *args, **kwargs)

        # Если владелец — разрешаем
        if hasattr(obj, 'owner') and obj.owner == user:
            return super().dispatch(request, *args, **kwargs)

        # Иначе — запрещаем
        return HttpResponseForbidden("Вы не можете редактировать или удалять чужие данные.")
