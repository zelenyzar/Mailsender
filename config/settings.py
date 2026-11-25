CELERY_BEAT_SCHEDULE = {
    "check-habits-every-5-minutes": {
        "task": "habit.tasks.check_habits",
        "schedule": 300.0,  # секунды
    },
}

После правки перезапустите оба процесса, чтобы Celery подхватил новую конфигурацию:

bash
celery -A config worker -l INFO
celery -A config beat -l INFO
