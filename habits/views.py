import logging

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Habit
from .pagination import HabitListPagination
from .permissions import IsOwner
from .serializers import HabitSerializer

logger = logging.getLogger(__name__)


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    pagination_class = HabitListPagination
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        habit = serializer.save(user=self.request.user)
        logger.info(
            "Создана привычка id=%s пользователь=%s (is_pleasant=%s)",
            habit.pk,
            self.request.user,
            habit.is_pleasant,
        )

    def perform_update(self, serializer):
        habit = serializer.save()
        logger.info(
            "Обновлена привычка id=%s пользователь=%s",
            habit.pk,
            self.request.user,
        )

    def perform_destroy(self, instance):
        logger.info(
            "Удалена привычка id=%s пользователь=%s",
            instance.pk,
            self.request.user,
        )
        instance.delete()

    @action(detail=False, methods=["get"])
    def public(self, request):
        queryset = Habit.objects.filter(is_public=True).order_by("-created_at")
        page = self.paginate_queryset(queryset)
        logger.info(
            "Запрос публичных привычек пользователем=%s (найдено %d)",
            request.user,
            queryset.count(),
        )
        serializer = self.get_serializer(
            page if page is not None else queryset, many=True
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)
