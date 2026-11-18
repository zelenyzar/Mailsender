from django.conf import settings
from django.db import models

class Habit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    place = models.CharField(max_length=255)
    time = models.CharField(max_length=255)
    action = models.CharField(max_length=500)
    is_pleasant = models.BooleanField(default=False)   # обязательно default
    related_habit = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    periodicity = models.PositiveIntegerField(default=1)  # дни
    reward = models.CharField(max_length=255, blank=True)
    duration = models.PositiveSmallIntegerField()         # минуты
    is_public = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'
