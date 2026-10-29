from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
import smtplib
from email.mime.text import MIMEText


#-----Client----
class Client(models.Model):
    email = models.EmailField(
        max_length=100,
        unique=True,
        verbose_name='Email',
        validators=[validate_email],
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

#----Message----
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


#----Mailing----
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
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('Дата начала должна быть строго раньше даты окончания.')

    def update_status(self):
        """Динамический пересчет статуса и сохранение его, если изменился"""
        now = timezone.now()
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

    def send(self):
        """Запуск рассылки. Возвращает кортеж: (успешно, список ошибок)"""
        now = timezone.now()

        if not (self.start_time <= now <= self.end_time):
            return False, ['Рассылка находится вне временного окна отправки']

        errors = []

        clients = self.recipients.all()
        if not clients.exists():
            return False, ['В рассылке нет получателей']
        subject = self.message.subject
        message = self.message.message or ''
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

        smtp_host = getattr(settings, 'EMAIL_HOST', 'localhost')
        smtp_port = getattr(settings, 'EMAIL_PORT', 25)
        smtp_user = getattr(settings, 'EMAIL_HOST_USER', '')
        smtp_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        use_tls = getattr(settings, 'EMAIL_USE_TLS', False)
        timeout = getattr(settings, 'EMAIL_TIMEOUT', 10)

        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=timeout) as server:
                if use_tls:
                    server.starttls()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)

                for client in clients:
                    msg = MIMEText(body, 'plain', 'utf-8')
                    msg['Subject'] = subject
                    msg['From'] = from_email
                    msg['To'] = client.email
                    try:
                        # send_message возвращает dict: {email: (code, response_text)}
                        response = server.send_message(msg)
                        MailingAttempt.objects.create(
                            mailing=self,
                            client=client,
                            status=MailingAttempt.STATUS_SUCCESS,
                            error_message='',
                            server_response=str(response),
                        )
                    except Exception as e:
                        error_text = str(e)
                        MailingAttempt.objects.create(
                            mailing=self,
                            client=client,
                            status=MailingAttempt.STATUS_FAIL,
                            error_message=error_text,
                            server_response='',
                        )
                        errors.append(f'{client.email}: {error_text}')

                success = len(errors) == 0
                return success, errors

            except smtplib.SMTPConnectError as e:
                error_text = f'Не удалось подключиться к SMTP: {e}'
                for client in clients:
                    MailingAttempt.objects.create(
                        mailing=self,
                        client=client,
                        status=MailingAttempt.STATUS_FAIL,
                        error_message=error_text,
                        server_response='',
                    )
                return False, [error_text]

class MailingAttempt(models.Model):
    """Модель для хранения истории попыток отправки"""
    STATUS_SUCCESS = 'Успешно'
    STATUS_FAIL = 'Не успешно'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Успешно'),
        (STATUS_FAIL, 'Не успешно'),
    ]

    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name='attempts',
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
    )

    error_message = models.TextField(
        blank=True,
        null=True,
        default='',
        verbose_name='Текст ошибки'
    )

    sent_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата отправки'
    )

    server_response = models.TextField(
        blank=True,
        null=True,
        verbose_name='Ответ почтового сервера',
        help_text='Код и текст ответа SMTP'
    )

    class Meta:
        verbose_name = 'Попытка рассылки'
        verbose_name_plural = 'Попытки рассылки'
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.mailing.id} -> {self.client.email} ({self.status})'
