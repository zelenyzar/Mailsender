from user.models import User
from django.core.management import BaseCommand

class Command(BaseCommand):
    help = 'Создает суперпользователя admin@example.com'

    def handle(self, *args, **options):
        # Проверяем, существует ли уже пользователь
        if User.objects.filter(email="admin@example.com").exists():
            self.stdout.write(self.style.WARNING('Пользователь уже существует'))
            return

        user = User.objects.create_superuser(
            email="admin@example.com",
            password="123qwe",
            first_name="Admin",
            last_name="Root"
        )
        user.is_active = True
        user.save()
        self.stdout.write(self.style.SUCCESS('Суперпользователь успешно создан!'))
