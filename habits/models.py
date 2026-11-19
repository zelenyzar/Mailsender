from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class Habit(models.Model):
    """Модель «Привычка»."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="habits",
        verbose_name="Создатель",
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
        return f"{self.user.username}: «{self.action[:40]}…» ({self.get_periodicity_display()})"

    def clean(self):
        super().clean()

        # Правило: полезная привычка ≤ 2 минут
        if not self.is_pleasant and self.duration_minutes > 2:
            raise ValidationError(
                {"duration_minutes": "Полезная привычка не должна занимать больше 2 минут."}
            )

        # Приятная привычка — это вознаграждение, у неё не должно быть связанной привычки
        if self.is_pleasant and self.related_habit is not None:
            raise ValidationError(
                {"related_habit": "Приятная привычка не может иметь поле «Связанная привычка»."}
            )

        # Опционально: если указана связанная привычка, она должна быть приятной
        if not self.is_pleasant and self.related_habit is not None:
            if not self.related_habit.is_pleasant:
                raise ValidationError(
                    {"related_habit": "В поле «Связанная привычка» можно указывать только приятные привычки."}
                )

    def full_clean(self, exclude=None, validate_unique=True):
        self.clean()
        super().full_clean(exclude=exclude, validate_unique=validate_unique)
