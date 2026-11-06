import logging

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache

from .models import Mailing, MailingAttempt

logger = logging.getLogger(__name__)


def update_mailing_statuses():
    Mailing.update_all_statuses()


def run_mailing_task(mailing_id):
    try:
        mailing = Mailing.objects.prefetch_related('recipients', 'message').get(pk=mailing_id)

        now = timezone.now()

        if mailing.status == Mailing.STATUS_BLOCKED:
            return {"status": "blocked", "message": "Рассылка заблокирована"}

        if now > mailing.end_time:
            mailing.status = Mailing.STATUS_COMPLETED
            mailing.save()
            return {"status": "completed", "message": "Время рассылки истекло"}

        clients = mailing.recipients.all()
        if not clients.exists():
            mailing.status = Mailing.STATUS_COMPLETED
            mailing.save()
            return {"status": "completed", "message": "Нет получателей"}

        subject = mailing.message.subject
        message_body = mailing.message.message or ''
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

        attempts_to_create = []
        success_count = 0
        error_count = 0

        for client in clients:
            try:
                send_mail(
                    subject=subject,
                    message=message_body,
                    from_email=from_email,
                    recipient_list=[client.email],
                    fail_silently=False,
                )

                attempts_to_create.append(
                    MailingAttempt(
                        mailing=mailing,
                        client=client,
                        status=MailingAttempt.STATUS_SUCCESS,
                        error_message='',
                        server_response='OK',
                        owner=mailing.owner
                    )
                )
                success_count += 1
            except Exception as e:
                error_text = str(e)
                attempts_to_create.append(
                    MailingAttempt(
                        mailing=mailing,
                        client=client,
                        status=MailingAttempt.STATUS_FAIL,
                        error_message=error_text,
                        server_response='',
                        owner=mailing.owner
                    )
                )
                error_count += 1

        if attempts_to_create:
            MailingAttempt.objects.bulk_create(attempts_to_create)

        mailing.status = Mailing.STATUS_COMPLETED
        mailing.save()

        # Сбрасываем кэш, чтобы статистика обновилась
        if mailing.owner_id:
            cache.delete('statistics_global')
            cache.delete(f'statistics_user_{mailing.owner_id}')
            cache.delete('mailing_list_all')
            cache.delete(f'mailing_list_{mailing.owner_id}')
            cache.delete(f'dashboard_{mailing.owner_id}')

        return {
            "status": "done",
            "success": success_count,
            "errors": error_count,
            "message": f"Отправлено: {success_count}, ошибок: {error_count}"
        }

    except Mailing.DoesNotExist:
        return {"status": "error", "message": "Рассылка не найдена"}
    except Exception:
        logger.exception("Ошибка в задаче рассылки #%s", mailing_id)
        return {"status": "error", "message": "Внутренняя ошибка"}
