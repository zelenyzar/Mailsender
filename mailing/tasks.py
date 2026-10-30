from django.utils import timezone
from .models import Mailing, MailingAttempt
from django.core.mail import send_mail
from django.conf import settings

def run_mailing_task(mailing_id):
    """
    Эта функция будет выполняться в отдельном воркер-процессе.
    Она НЕ должна возвращать HTML или делать redirect. Только логику.
    """
    try:
        # Получаем рассылку. Важно: используем select_related/prefetch_related, 
        # чтобы не делать лишних запросов в цикле.
        mailing = Mailing.objects.prefetch_related('recipients', 'message').get(pk=mailing_id)
        
        now = timezone.now()
        
        # Проверка условий запуска
        if mailing.status == Mailing.STATUS_BLOCKED:
            return {"status": "blocked", "message": "Рассылка заблокирована"}
        
        if not (mailing.start_time <= now <= mailing.end_time):
            # Если время вышло, можно сразу пометить как завершенную
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

        # Массово сохраняем попытки (быстрее)
        if attempts_to_create:
            MailingAttempt.objects.bulk_create(attempts_to_create)

        # Обновляем статус рассылки
        if error_count == 0:
            mailing.status = Mailing.STATUS_COMPLETED
        else:
            # Можно оставить RUNNING, если планируешь досылать позже, 
            # или поставить COMPLETED, если считаем, что попытка сделана
            mailing.status = Mailing.STATUS_COMPLETED 
            
        mailing.save()

        return {
            "status": "done",
            "success": success_count,
            "errors": error_count,
            "message": f"Отправлено: {success_count}, ошибок: {error_count}"
        }

    except Mailing.DoesNotExist:
        return {"status": "error", "message": "Рассылка не найдена"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
