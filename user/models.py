from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Описание полей модели пользвателя"""

    username = None
    email = models.EmailField(unique=True, verbose_name="email")
    phone = models.CharField(
        max_length=15,
        verbose_name="телефон",
        blank=True,
        null=True,
        help_text="Введите номер телефона",
    )
    avatar = models.ImageField(
        upload_to="users/avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар",
        help_text="Загрузите свое фото",
    )
    city = models.TextField(
        max_length=15,
        verbose_name="город",
        blank=True,
        null=True,
        help_text="Введите из какого вы города",
    )
    chat_id = models.CharField(
        max_length=255, verbose_name="chat_id", null=True, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
