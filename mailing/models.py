from django.db import models

from django.core.exceptions import ValidationError
from django.utils import timezone

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
    verbose_name='Сообщение',
    help_text='введите текст сообщения'
  )

  class Meta:
  verbose_name = 'Сообщение'
  verbose_name_plural = 'Сообщения'
  ordering = ['subject']

  def __str__(self):
  return self.subject
  
class Mailing(models.Model):
  STATUS_CREATED = 'Создана'
  STATUS_RUNNING = 'Запущена'
  STATUS_COMPLETED = 'Завершена'

  STATUS_CHOICES = [
    (STATUS_CREATED, 'Создана'),
    (STATUS_RUNNING, 'Запущена'),
    (STATUS_COMPLETED, 'Завершена'),
  ]

  start_time = models.DateTimeField(
    verbose_name='Дата и время начала отправки',
    help_text='С какого момента рассылка будет запущена'
  )

  end_time = models.DateTimeField(
    verbose_name='Дата и время окончания отправки',
    help_text='До какого момента разрешено выполнять отправку'
  )

  status = models.CharField(
    max_length=20,
    choices=STATUS_CHOICES,
    default=STATUS_CREATED,
    verbose_name='Статус',
    editable=False
  )

  message = models.ForeignKey(
    Message,
    on_delete=models.CASCADE,
    related_name='mailings',
    verbose_name='Сообщение'
  )

  recipients = models.ManyToManyField(
    Client,
    related_name='mailings',
    verbose_name='Получатели'
  )

  class Meta:
    verbose_name = 'Рассылка'
    verbose_name_plural = 'Рассылки'
    ordering = ['-start_time']

  def __str__(self):
    return f'Рассылка #{self.pk} ({self.status})'

  def clean(self):
    """Валидация на уровне модели"""
    now = timezon.now()
    if self.start_time and self.start_time < now:
      raise ValidationError('Дата начала должна быть раньше даты окончания.')

  def update_status(self):
    """Динамический пересчет статуса и сохранение его, если изменился"""
    now = timezon.now()
    new_status = self.status

    if now < self.start_time:
      new_status = self.STATUS_CREATED
    elif now <= self.end_time:
      new_status = self.STATUS_RUNNING
    else:
      new_status = self.STATUS_COMPLETED

    if new_status != self.status:
      self.status = new_status
      self.save(update_fields=['status'])

  def save(self, *args, **kwargs):
    self.full_clean()
    super().save(*args, **kwargs)

  
