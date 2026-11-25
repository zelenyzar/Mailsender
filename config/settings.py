LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} [{levelname}] {name}: {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "{levelname}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "app.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 МБ на файл
            "backupCount": 3,             # хранить 3 старых файла
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "telegram_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "telegram.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 3,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "habit": {                      # ваше приложение
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "habit.tasks": {                # задачи Celery — отдельный файл
            "handlers": ["console", "telegram_file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {             # ошибки запросов (500 и т. п.)
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": True,
        },
        "django.core.mail": {           # отправка почты
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}
