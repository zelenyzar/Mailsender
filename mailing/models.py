from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

User = get_user_model()

class Client(models.Model):
    email = models.EmailField(
        max_length=100, unique=True, verbose_name='Email',
        validators=[validate_email], help_text='введите почту клиента'
    )
    full_name = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Ф.И.О.', help_text='введите Ф.И.О. полностью'
    )
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    # ДОБАВЛЕНО: Владелец клиента
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='clients', 
        verbose_name='Владелец', editable=False
    )

    class Meta:
        verbose_name = 'Получатель рассылки'
        verbose_name_plural = 'Получатели рассылки'
        ordering = ['email']
        # Уникальность email теперь только в рамках владельца (опционально, зависит от бизнеса)
        # Если email должен быть глобально уникальным, оставь unique=True в поле email.
        # Если можно иметь одинаковых клиентов у разных пользователей, убери unique=True из email.

    def __str__(self):
        return f"{self.email} ({self.owner.username})"


class Message(models.Model):
    subject = models.CharField(max_length=100, verbose_name='Тема письма')
    message = models.TextField(blank=True, null=True, verbose_name='Сообщение')
    # ДОБАВЛЕНО: Владелец сообщения
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='messages', 
        verbose_name='Владелец', editable=False
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
    # Статус для менеджеров (блокировка)
    STATUS_BLOCKED = 'Заблокирована' 

    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создана'),
        (STATUS_RUNNING, 'Запущена'),
        (STATUS_COMPLETED, 'Завершена'),
        (STATUS_BLOCKED, 'Заблокирована'),
    ]

    start_time = models.DateTimeField(verbose_name='Дата и время начала отправки')
    end_time = models.DateTimeField(verbose_name='Дата и время окончания отправки')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default=STATUS_CREATED, verbose_name='Статус', editable=False
    )
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name='mailings', verbose_name='Сообщение'
    )
    recipients = models.ManyToManyField(
        Client, related_name='mailings', verbose_name='Получатели'
    )
    # ДОБАВЛЕНО: Владелец рассылки
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='mailings', 
        verbose_name='Владелец', editable=False
    )

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        ordering = ['-start_time']

    def __str__(self):
        return f'Рассылка #{self.pk} ({self.status})'

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('Дата начала должна быть строго раньше даты окончания.')
            
    def save(self, *args, **kwargs):
        # Автоматически обновляем статус при сохранении, если нужно
        self.update_status()
        super().save(*args, **kwargs)

    def update_status(self):
        now = timezone.now()
        new_status = self.status

        # Не меняем статус, если рассылка заблокирована менеджером
        if self.status == self.STATUS_BLOCKED:
            return

        if now < self.start_time:
            new_status = self.STATUS_CREATED
        elif now <= self.end_time:
            new_status = self.STATUS_RUNNING
        else:
            new_status = self.STATUS_COMPLETED

        if new_status != self.status:
            self.status = new_status
            # Используем update_fields, чтобы не вызывать save() рекурсивно и не триггерить лишние проверки
            from django.db import transaction
            with transaction.atomic():
                Mailing.objects.filter(pk=self.pk).update(status=new_status)
                self.status = new_status # Обновляем локальный объект

    def send(self):
        """
        Запуск рассылки.
        """
        now = timezone.now()

        # Проверка статуса блокировки
        if self.status == self.STATUS_BLOCKED:
            return False, ['Рассылка заблокирована администратором']

        if not (self.start_time <= now <= self.end_time):
            return False, ['Рассылка находится вне временного окна отправки']

        clients = self.recipients.all()
        if not clients.exists():
            return False, ['В рассылке нет получателей']

        subject = self.message.subject
        message_body = self.message.message or ''
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

        errors = []

        for client in clients:
            try:
                send_mail(
                    subject=subject,
                    message=message_body,
                    from_email=from_email,
                    recipient_list=[client.email],
                    fail_silently=False,
                )

                MailingAttempt.objects.create(
                    mailing=self,
                    client=client,
                    status=MailingAttempt.STATUS_SUCCESS,
                    error_message='',
                    server_response='OK (через Django backend)',
                    owner=self.owner # Наследуем владельца от рассылки
                )
            except Exception as e:
                error_text = str(e)
                errors.append(f'{client.email}: {error_text}')
                MailingAttempt.objects.create(
                    mailing=self,
                    client=client,
                    status=MailingAttempt.STATUS_FAIL,
                    error_message=error_text,
                    server_response='',
                    owner=self.owner
                )

        success = len(errors) == 0
        return success, errors


class MailingAttempt(models.Model):
    STATUS_SUCCESS = 'Успешно'
    STATUS_FAIL = 'Не успешно'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Успешно'),
        (STATUS_FAIL, 'Не успешно'),
    ]

    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name='attempts')
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True, null=True, default='', verbose_name='Текст ошибки')
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')
    server_response = models.TextField(blank=True, null=True, verbose_name='Ответ почтового сервера')
    
    # ДОБАВЛЕНО: Владелец попытки (для фильтрации статистики)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='attempts', 
        verbose_name='Владелец', editable=False, null=True
    )

    class Meta:
        verbose_name = 'Попытка рассылки'
        verbose_name_plural = 'Попытки рассылки'
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.mailing.id} -> {self.client.email} ({self.status})'
