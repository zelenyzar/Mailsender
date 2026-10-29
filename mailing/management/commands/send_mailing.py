from django.core.management import BaseCommand, CommandError
from mailing.models import Mailing


class Command(BaseCommand):
    help = 'Запускает указанную рассылку вручную'

    def add_arguments(self, parser):
        parser.add_argument('mailing_id', type=int, help='ID рассылки для отправки')

    def handle(self, *args, **options):
        mailing_id = options['mailing_id']
        try:
            mailing = Mailing.objects.get(pk=mailing_id)
        except Mailing.DoesNotExist:
            raise CommandError(f'Рассылка с ID {mailing_id} не найдена')

        now = timezone.now()

        if not (mailing.start_time <= now <= mailing.end_time):
            self.stdout.write(self.style.ERROR(
                f'Рассылка #{mailing_id} НЕ может быть запущена: '
                f'текущее время ({now}) вне окна отправки '
                f'[{mailing.start_time} — {mailing.end_time}]'
            ))
            return

        mailing.update_status()

        self.stdout.write(f'Попытка запуска рассылки {mailing_id}...')
        success, errors = mailing.send()

        total_attempts = mailing.attempts.count()
        failed_count = mailing.attempts.filter(status='Не успешно').count()

        if success:
            self.stdout.write(
                self.style.SUCCESS(f'Рассылка #{mailing_id} успешно отправлена! (всего попыток: {total_attempts})'))
        else:
            self.stdout.write(self.style.ERROR(
                f'Частичная ошибка в рассылке #{mailing_id}: {len(errors)} ошибок из {total_attempts} попыток.'))
            for err in errors:
                self.stdout.write(f' - {err}')
