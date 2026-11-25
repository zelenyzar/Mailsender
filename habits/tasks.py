import logging

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import Habit

logger = logging.getLogger(__name__)

API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


@shared_task
def send_habit_reminder(habit_id):
    """Отправка напоминания о конкретной привычке."""
    habit = Habit.objects.select_related("user__profile").filter(pk=habit_id).first()
    if habit is None:
        logger.warning("send_habit_reminder: привычка id=%s не найдена", habit_id)
        return

    profile = getattr(habit.user, "profile", None)
    chat_id = profile.tg_chat_id if profile else ""
    if not chat_id:
        logger.info("send_habit_reminder: у habit=%s нет tg_chat_id, отправка пропущена", habit_id)
        return

    message = (
        f"⏰ Пора выполнить привычку!\n"
        f"Я буду {habit.action} в {habit.time.strftime('%H:%M')} "
        f"({habit.place})."
    )

    try:
        response = requests.post(
            f"{API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )
        response.raise_for_status()
        logger.info("Напоминание отправлено: habit=%s chat_id=%s", habit_id, chat_id)
    except requests.RequestException:
        logger.exception("Ошибка отправки в Telegram (habit=%s)", habit_id)


@shared_task
def check_habits():
    """Проверка: какие привычки пора выполнять прямо сейчас.

    Запускается Celery Beat каждые 5 минут.
    """
    now = timezone.localtime()
    current_time = now.time().replace(second=0, microsecond=0)
    sent = 0

    for habit in Habit.objects.select_related("user__profile"):
