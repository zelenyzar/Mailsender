from rest_framework.serializers import ModelSerializer

from users.models import User


class UserSerializer(ModelSerializer):
    """Класс сериализатора для модели пользователя"""

    class Meta:
        model = User
        fields = "__all__"
