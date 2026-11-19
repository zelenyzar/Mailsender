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

    @staticmethod
    def _strip_reward(value):
        return value.strip() if isinstance(value, str) else ""

    def validate(self, attrs):
        # Текущее значение (для PATCH), если поле не передано
        is_pleasant = attrs.get(
            "is_pleasant",
            getattr(self.instance, "is_pleasant", False) if self.instance else False,
        )
        related = attrs.get("related_habit")
        reward = attrs.get("reward", "") or ""
        reward_str = self._strip_reward(reward)
        duration = attrs.get("duration_minutes", 0)
        periodicity = attrs.get("periodicity", 1)

        # 4. Приятная: нет reward, нет related_habit
        if is_pleasant:
            if reward_str:
                raise serializers.ValidationError(
                    {"reward": "У приятной привычки не может быть вознаграждения."}
                )
            if related is not None:
                raise serializers.ValidationError(
                    {"related_habit": "У приятной привычки не может быть связанной привычки."}
                )

        # Полезные привычки
        if not is_pleasant:
            # 1. XOR: related_habit и reward — не одновременно
            if related is not None and reward_str:
                raise serializers.ValidationError(
                    {
                        "related_habit": "Нельзя указывать и связанную привычку, и вознаграждение одновременно. Выберите что-то одно.",
                        "reward": "Нельзя указывать и связанную привычку, и вознаграждение одновременно. Выберите что-то одно.",
                    }
                )

            # 3. Связанная должна быть приятной
            if related is not None and not related.is_pleasant:
                raise serializers.ValidationError(
                    {"related_habit": "В связанные привычки могут попадать только приятные привычки."}
                )

        # 5, 6. Периодичность: 1–7 дней (7 = «раз в неделю», допустимо; 14 — нет)
        if not (1 <= periodicity <= 7):
            raise serializers.ValidationError(
                {
                    "periodicity": "Периодичность должна быть от 1 до 7 дней "
                    "(нельзя выполнять реже 1 раза в 7 дней)."
                }
            )

        # 2. Длительность ≤ 2 мин (120 с)
        if duration > 2:
            raise serializers.ValidationError(
                {"duration_minutes": "Время выполнения не должно превышать 120 секунд (2 минуты)."}
            )

        return attrs
