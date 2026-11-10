from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

from celery.schedules import crontab


# Установка переменной окружения для настроек проекта
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Создание экземпляра объекта Celery
app = Celery("config")

# Загрузка настроек из файла Django
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматическое обнаружение и регистрация задач из файлов tasks.py в приложениях Django
app.autodiscover_tasks()

app.conf.update(
    timezone="Europe/Moscow",
    enable_utc=False,
    # либо: enable_utc=True и timezone="UTC" — тогда все расписания в UTC
)

app.conf.beat_schedule = {
    "deactivate-inactive-users-daily": {
        "task": "users.tasks.deactivate_inactive_users",
        "schedule": crontab(hour=3, minute=0),
        "args": (),
    },
}
