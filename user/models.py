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
