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
