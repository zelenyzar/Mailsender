from rest_framework import serializers
from .models import Habit


class HabitNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = ["id", "action", "is_pleasant", "place", "time"]


class HabitSerializer(serializers.ModelSerializer):
    related_habit = HabitNestedSerializer(read_only=True)

    class Meta:
        model = Habit
        fields = [
            "id",
            "user",
            "action",
            "place",
            "time",
            "is_pleasant",
            "related_habit",
            "periodicity",
            "reward",
            "duration_minutes",
            "is_public",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]

    def create(self, validated_data):
        # Берём пользователя из контекста (из request), а не из JSON
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, attrs):
        # Проверка при создании/обновлении (DRF)
        is_pleasant = attrs.get("is_pleasant", self.instance.is_pleasant if self.instance else False)
        related = attrs.get("related_habit")

        if is_pleasant and related is not None:
            raise serializers.ValidationError(
                {"related_habit": "Приятная привычка не может иметь связанную привычку."}
            )

        if not is_pleasant and related is not None:
            if not related.is_pleasant:
                raise serializers.ValidationError(
                    {"related_habit": "В поле «Связанная привычка» допустимы только приятные привычки."}
                )

        if not is_pleasant and related is None and not attrs.get("reward"):
            # Можно сделать это обязательным на уровне бизнес-логики (по желанию)
            pass

        return attrs
