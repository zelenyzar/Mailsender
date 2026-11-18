from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import AllowAny

from users.models import User
from users.serializers import UserSerializer


class UserCreateApiView(CreateAPIView):
    """Контроллер создания экземпляра пользователя"""

    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (
        AllowAny,
    )  # для этого контроллера доступ для всех неавторизованных пользователей

    def perform_create(self, serializer):
        user = serializer.save(is_active=True)
        user.set_password(
            user.password
        )  # хешируем пароль пользователя, чтобы не хранить его в открытом виде
        user.save()


class UserListApiView(ListAPIView):
    """Контроллер для вывода списка пользователей"""

    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserRetrieveApiView(RetrieveAPIView):
    """Класс контроллера для вывода экземпляра пользователя"""

    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserUpdateApiView(UpdateAPIView):
    """Класс контроллера для изменения экземпляра пользователя"""

    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDestroyApiView(DestroyAPIView):
    """Класс контроллера для удаления экземпляра пользователя"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
