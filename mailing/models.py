from django.db import models

class Client(models.Model):
  email = models.EmailField(
    max_length=100,
    unique=True,
    verbose_name='Email',
    help_text='введите почту клиента'
  )

  full_name = models.CharField(
    max_length=100,
    blank=True,
    null=True,
    verbose_name='Ф.И.О.',
    help_text='введите Ф.И.О. полностью'
  )

  comment = models.TextField(
    blank=True,
    null=True,
    verbose_name='Комментарий'
  )

class Meta:
  verbose_name = 'Получатель рассылки'
  verbose_name_plural = 'Получатели рассылки'
  ordering = ['email']

def __str__(self):
  return self.email

class Message(models.Model):
  subject = models.CharField(
    max_length=100,
    verbose_name='Тема письма',
    help_text='введите тему письма'
  )

  message = models.TextField(
    blank=True,
    null=True,
    verbose_name='введите текст сообщения'
  )
  

