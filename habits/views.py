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

from rest_framework import viewsets, permissions, mixins
from .models import Habit
from .serializers import HabitSerializer
from .permissions import IsOwnerOrPublic


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    pagination_class = HabitListPagination   # (или глобальная REST_FRAMEWORK → PAGE_SIZE: 5)

    # === ЛИЧНЫЕ ===
    def get_queryset(self):
        if self.action in ('list', 'retrieve'):
            return Habit.objects.filter(user=self.request.user).order_by('-created_at')
        return Habit.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrPublic]

    # === ПУБЛИЧНЫЕ ===
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def public(self, request):
        # Важно: здесь НЕ используем get_queryset(), потому что он фильтрует по user=request.user
        queryset = Habit.objects.filter(is_public=True).order_by('-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = HabitSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = HabitSerializer(queryset, many=True, context={'request': request})
        return self.get_response(serializer.data)

