from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class User(AbstractUser):
    """
    Кастомная модель пользователя.
    Используем email как логин.
    """
    email = models.EmailField(unique=True, verbose_name='Email')
    
    # Поле для токена подтверждения регистрации
    verification_token = models.CharField(max_length=32, null=True, blank=True)
    
    # Дата истечения токена
    token_expires_at = models.DateTimeField(null=True, blank=True)

    # Переопределяем username, чтобы он не был обязательным для формы, 
    # но оставался в базе данных для совместимости с Django Auth
    username = None 
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
