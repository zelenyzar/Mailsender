from django.contrib.auth.models import AbstractUser
from django.db import models

class Users(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name='Email')

    phone = models.CharField(max_length=35, verbose_name='Телефон', blank=True, null=True, help_text='Введите номер телефона')
    country = models.CharField(max_length=56,verbose_name='Страна', blank=True, null=True, help_text='Введите страну')
    avatar = models.ImageField(upload_to='user/avatar/',verbose_name='Аватар', blank=True, null=True, help_text='Загрузите свой аватар')

    token = models.CharField(max_length=100, blank=True, null=True, verbose_name='Token')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email
