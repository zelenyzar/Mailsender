from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class Habit(models.Model):
    """Модель «Привычка»."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='habits'
    )

    place = models.CharField(
        "Место",
        max_length=255,
    )

    time = models.TimeField(
        "Время",
    )

    action = models.CharField(
        "Действие",
        max_length=500,
        # Формат: «я буду [ДЕЙСТВИЕ] в [ВРЕМЯ] в [МЕСТО]»
    )

    is_pleasant = models.BooleanField(
        "Признак приятной привычки",
        default=False,
    )

    related_habit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_to",
        verbose_name="Связанная привычка",
    )

    periodicity = models.PositiveSmallIntegerField(
        "Периодичность (в днях)",
        default=1,  # 1 день = ежедневно
    )

    reward = models.CharField(
        "Вознаграждение",
        max_length=255,
        blank=True,
        default="",
    )

    duration_minutes = models.PositiveSmallIntegerField(
        "Время на выполнение (мин)",
    )

    is_public = models.BooleanField(
        "Признак публичности",
        default=False,
    )

    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
        read_only=True,
    )

    updated_at = models.DateTimeField(
        "Дата обновления",
        auto_now=True,
        read_only=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"

    def __str__(self):
        return f"{self.user.username}: «{self.action[:40]}…»"

    def _strip_reward(self, value):
        return value.strip() if isinstance(value, str) else ""

    def clean(self):
        super().clean()

        # 2. Время ≤ 120 с = 2 мин
        if self.duration_minutes > 2:
            raise ValidationError(
                {"duration_minutes": "Время выполнения не должно превышать 120 секунд (2 минуты)."}
            )

        # 4. Приятная привычка: без вознаграждения и без связанной привычки
        if self.is_pleasant:
            if self._strip_reward(self.reward):
                raise ValidationError(
                    {"reward": "У приятной привычки не может быть вознаграждения."}
                )
            if self.related_habit is not None:
                raise ValidationError(
                    {"related_habit": "У приятной привычки не может быть связанной привычки."}
                )

        # Для полезных привычек
        if not self.is_pleasant:
            # 3. Связанная привычка должна быть приятной
            if self.related_habit is not None and not self.related_habit.is_pleasant:
                raise ValidationError(
                    {"related_habit": "В связанные привычки могут попадать только приятные привычки."}
                )

            # 1. XOR: не одновременно related_habit и reward
            if self.related_habit is not None and self._strip_reward(self.reward):
                raise ValidationError(
                    {
                        "related_habit": "Нельзя указывать и связанную привычку, и вознаграждение одновременно. Выберите что-то одно.",
                        "reward": "Нельзя указывать и связанную привычку, и вознаграждение одновременно. Выберите что-то одно.",
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
