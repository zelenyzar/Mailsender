# # Создать менеджера с паролем по умолчанию
# python manage.py create_manager alice

# # Создать менеджера с кастомным email и паролем
# python manage.py create_manager bob --email bob@test.com --password SuperSecret123

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

class Command(BaseCommand):
    help = "Создает менеджера: создает пользователя (если нет), группу 'manager', добавляет пользователя в группу."

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Имя пользователя (username)')
        parser.add_argument('--email', type=str, required=False, default=None,
                            help='Email пользователя (по умолчанию username@example.com)')
        parser.add_argument('--password', type=str, default='password123',
                            help='Пароль пользователя (по умолчанию: password123)')

    def handle(self, *args, **options):
        username = options['username']
        email = options.get('email') or f"{username}@example.com"
        password = options['password']

        # Создаем группу manager, если её нет
        group, created = Group.objects.get_or_create(name='manager')
        if created:
            self.stdout.write(self.style.SUCCESS('Группа "manager" создана.'))
        else:
            self.stdout.write('Группа "manager" уже существует.')

        # Пытаемся получить или создать пользователя
        user, user_created = User.objects.get_or_create(username=username, defaults={'email': email})
        if user_created:
            # Если пользователь создан, задаем пароль
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Пользователь "{username}" создан с паролем "{password}".'))
        else:
            self.stdout.write(f'Пользователь "{username}" уже существует. Пароль не изменён.')

        # Добавляем в группу
        if not user.groups.filter(name='manager').exists():
            user.groups.add(group)
            self.stdout.write(self.style.SUCCESS(f'Пользователь "{username}" добавлен в группу "manager".'))
        else:
            self.stdout.write(f'Пользователь "{username}" уже состоит в группе "manager".')
