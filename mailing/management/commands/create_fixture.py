Шаг 2. Запусти команду
python manage.py create_fixture
или с указанием своего пути:
python manage.py create_fixture --output mailing/fixtures/my_fixture.json


# mailing/management/commands/create_fixture.py
import json
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core import serializers
from mailing.models import Client, Message, Mailing, MailingAttempt

class Command(BaseCommand):
    help = 'Создаёт тестовые данные с "свежими" датами и сохраняет JSON-фикстуру. Можно исключить отдельные модели.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='mailing/fixtures/test_data.json',
            help='Путь к выходному JSON-файлу (по умолчанию: mailing/fixtures/test_data.json)'
        )
        parser.add_argument(
            '--exclude',
            nargs='+',
            choices=['clients', 'messages', 'mailings', 'attempts'],
            default=[],
            help='Модели для исключения из фикстуры. Примеры: --exclude mailings attempts'
        )
        parser.add_argument(
            '--fresh-dates',
            action='store_true',
            help='Генерировать даты относительно текущего времени (по умолчанию включено)'
        )

    def handle(self, *args, **options):
        output_path = options['output']
        exclude_list = options['exclude']
        use_fresh_dates = options.get('fresh_dates', True)

        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        now = timezone.now()

        # --- Клиенты ---
        clients = []
        if 'clients' not in exclude_list:
            for i in range(1, 6):
                client, _ = Client.objects.get_or_create(
                    email=f'client{i}@example.com',
                    defaults={
                        'full_name': f'Клиент {i}',
                        'comment': f'Тестовый получатель #{i}'
                    }
                )
                clients.append(client)
            self.stdout.write(self.style.SUCCESS(f'Создано {len(clients)} клиентов'))

        # --- Сообщения ---
        messages = []
        if 'messages' not in exclude_list:
            subjects = [
                'Приветствие: Добро пожаловать!',
                'Акция: Скидка 20% только сегодня',
                'Отчёт за месяц: Ваши результаты'
            ]
            bodies = [
                'Здравствуйте, {{ name }}! Рады видеть вас в нашей рассылке.',
                'Только сегодня у нас действует скидка 20%. Успейте воспользоваться!',
                'Вот ваши показатели за прошедший месяц. Подробнее в личном кабинете.'
            ]

            for subj, body in zip(subjects, bodies):
                msg, _ = Message.objects.get_or_create(
                    subject=subj,
                    defaults={'message': body}
                )
                messages.append(msg)
            self.stdout.write(self.style.SUCCESS(f'Создано {len(messages)} сообщений'))

        # --- Рассылки (с "свежими" датами) ---
        mailings = []
        if 'mailings' not in exclude_list:
            if use_fresh_dates:
                # Рассылка в будущем (статус «Создана»)
                m1 = Mailing.objects.create(
                    start_time=now + timedelta(days=2),
                    end_time=now + timedelta(days=5),
                    message=messages[0],
                    status='Создана'
                )
                m1.recipients.set(clients[:3])
                mailings.append(m1)

                # Активная рассылка (статус «Запущена»)
                m2 = Mailing.objects.create(
                    start_time=now - timedelta(hours=1),
                    end_time=now + timedelta(days=1),
                    message=messages[1],
                    status='Запущена'
                )
                m2.recipients.set(clients[1:])
                mailings.append(m2)

                # Завершенная рассылка (статус «Завершена»)
                m3 = Mailing.objects.create(
                    start_time=now - timedelta(days=3),
                    end_time=now - timedelta(days=1),
                    message=messages[2],
                    status='Завершена'
                )
                m3.recipients.set(clients)
                mailings.append(m3)
            else:
                # Если не нужны свежие даты — фиксированные (для стабильных тестов)
                from django.utils.dateparse import parse_datetime
                base_dt = parse_datetime('2024-11-15T10:00:00+03:00')
                if base_dt is None:
                    base_dt = now

                m1 = Mailing.objects.create(
                    start_time=base_dt + timedelta(days=2),
                    end_time=base_dt + timedelta(days=5),
                    message=messages[0],
                    status='Создана'
                )
                m1.recipients.set(clients[:3])
                mailings.append(m1)

                m2 = Mailing.objects.create(
                    start_time=base_dt,
                    end_time=base_dt + timedelta(days=1),
                    message=messages[1],
                    status='Запущена'
                )
                m2.recipients.set(clients[1:])
                mailings.append(m2)

                m3 = Mailing.objects.create(
                    start_time=base_dt - timedelta(days=3),
                    end_time=base_dt - timedelta(days=1),
                    message=messages[2],
                    status='Завершена'
                )
                m3.recipients.set(clients)
                mailings.append(m3)

            self.stdout.write(self.style.SUCCESS(f'Создано {len(mailings)} рассылок'))

        # --- Попытки отправки ---
        attempts = []
        if 'attempts' not in exclude_list and mailings:
            # Берём вторую рассылку (активную) и делаем пару попыток
            active_mailing = mailings[1] if len(mailings) > 1 else mailings[0]

            # Успешная попытка
            a1 = MailingAttempt.objects.create(
                mailing=active_mailing,
                client=clients[0],
                status='Успешно',
                server_response='OK'
            )
            attempts.append(a1)

            # Неуспешная попытка
            a2 = MailingAttempt.objects.create(
                mailing=active_mailing,
                client=clients[1],
                status='Не успешно',
                error_message='SMTP Error: user not found',
                server_response='550 User unknown'
            )
            attempts.append(a2)
            self.stdout.write(self.style.SUCCESS(f'Создано {len(attempts)} попыток отправки'))

        # --- Сериализация в JSON ---
        qs = Client.objects.none()
        if 'clients' not in exclude_list:
            qs = qs | Client.objects.all()
        if 'messages' not in exclude_list:
            qs = qs | Message.objects.all()
        if 'mailings' not in exclude_list:
            qs = qs | Mailing.objects.all()
        if 'attempts' not in exclude_list:
            qs = qs | MailingAttempt.objects.all()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(serializers.serialize('json', qs, indent=2))

        self.stdout.write(
            self.style.SUCCESS(f'Фикстура сохранена в: {output_path}')
        )
