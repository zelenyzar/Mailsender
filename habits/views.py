from rest_framework import viewsets
from .models import Habit
from .serializers import HabitSerializer
from .pagination import HabitListPagination


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    pagination_class = HabitListPagination

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

from rest_framework import viewsets, permissions

from .models import Habit
from .serializers import HabitSerializer
from .permissions import IsOwner
from .pagination import HabitListPagination


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    pagination_class = HabitListPagination
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    # --- Личные привычки (CRUD) ---
    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # --- Публичные привычки (только чтение) ---
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def public(self, request):
        queryset = Habit.objects.filter(is_public=True).order_by('-created_at')
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = HabitSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = HabitSerializer(queryset, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

