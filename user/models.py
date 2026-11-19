from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model


class UserManager(models.Manager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError("Email must be provided")
        user = self.create_user(username, email, password)
        user.set_password(password)
        user.save()
        return user


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )

    city = models.CharField("Город", max_length=100, blank=True)
    # … другие поля, не связанные с логином/паролем

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"Profile of {self.user.username}"
