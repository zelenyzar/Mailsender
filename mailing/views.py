from django.contrib.messages import success
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .forms import MailingForm
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import django_rq
from .tasks import run_mailing_task

from mailing.models import Client, Message, Mailing, MailingAttempt


# --- Clients ---
class ClientListView(OwnerOrManagerMixin, ListView):
    model = Client

class ClientDetailView(DetailView):
    model = Client


class ClientCreateView(CreateView):
    model = Client
    form_class = ClientForm

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ClientUpdateView(OwnerCheckMixin, UpdateView):
    model = Client
    form_class = ClientForm


class ClientDeleteView(OwnerCheckMixin, DeleteView):
    model = Client
    template_name = 'includes/confirm_delete.html' 
    success_url = '/clients/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        
        context['object_name'] = f"получателя {obj.email}"
        context['warning_message'] = (
            "Это действие нельзя отменить. Будут удалены все связи "
            "этого получателя с рассылками."
        )
        context['cancel_url'] = self.request.GET.get('next', self.success_url)
        
        return context


# --- Message ---
class MessageListView(ListView):
    model = Message


class MessageDetailView(DetailView):
    model = Message


class MessageCreateView(CreateView):
    model = Message
    form_class = MessageForm
    success_url = reverse_lazy('mailing:message_list')


class MessageUpdateView(UpdateView):
    model = Message
    form_class = MessageForm
    success_url = reverse_lazy('mailing:message_list')


class MessageDeleteView(DeleteView):
    model = Message
    template_name = 'includes/confirm_delete.html'
    success_url = reverse_lazy('mailing:message_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()

        context['object_name'] = f"сообщение «{obj.subject}»"
        context['warning_message'] = "Вы уверены? Это сообщение больше не будет доступно для выбора в рассылках."
        context['cancel_url'] = self.request.GET.get('next', self.success_url)

        return context


# --- Mailing ---
class MailingListView(OwnerOrManagerMixin, ListView):
    model = Mailing


class MailingDetailView(DetailView):
    model = Mailing

    def get_queryset(self):
        # Заранее загружаем связанные попытки отправки (MailingAttempt)
        return super().get_queryset().prefetch_related('attempts')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()  # пересчет и сохранение статуса при просмотре
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object = context['object']
        total_attempts = object.attempts.count()
        success_attempts = object.attempts.filter(
            status=MailingAttempt.STATUS_SUCCESS
        ).count()
        fail_attempts = total_attempts - success_attempts

        context['total_attempts'] = total_attempts
        context['success_attempts'] = success_attempts
        context['fail_attempts'] = fail_attempts

        return context

class MailingCreateView(CreateView):
    model = Mailing
    form_class = MailingForm

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages_list'] = Message.objects.all()
        context['clients_list'] = Client.objects.all()
        context['recipient_ids'] = []
        return context


class MailingUpdateView(OwnerCheckMixin, UpdateView):
    model = Mailing
    form_class = MailingForm

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.update_status()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages_list'] = Message.objects.all()
        context['clients_list'] = Client.objects.all()

        if self.object:
            context['recipient_ids'] = list(self.object.recipients.values_list('id', flat=True))
        else:
            context['recipient_ids'] = []
        return context


class MailingDeleteView(OwnerCheckMixin, DeleteView):
    model = Mailing
    template_name = 'includes/confirm_delete.html'
    success_url = '/mailings/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()

        context['object_name'] = f"рассылку #{obj.pk}"
        context['warning_message'] = (
            "Внимание: будут удалены сама рассылка, все попытки отправки "
            "(логи ошибок, статусы) и связи с получателями. Восстановить невозможно."
        )
        context['cancel_url'] = self.request.GET.get('next', self.success_url)

        return context


def mailing_send(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    if request.method == 'POST':
        success, errors = mailing.send()
        if success:
            messages.success(request, f'Рассылка #{mailing.pk} успешно отправлена всем получателям!')
        else:
            error_text = '\n'.join(errors)
            messages.error(request, f'Частичная ошибка при отправке рассылки #{mailing.pk}:\n{error_text}')
        return redirect('mailing:mailing_detail', pk=mailing.pk)
    return redirect('mailing:mailing_detail', pk=mailing.pk)

# --- Dashboard ---
def dashboard(request):
    now = timezone.now()

    context = cache.get_or_set(
        f'dashboard_{request.user.pk}',
        lambda: {
            'total_mailings': Mailing.objects.count(),
            'unique_recipients': Client.objects.count(),
            'active_mailings': Mailing.objects.filter(
                start_time__lte=now,
                end_time__gte=now
            ).count(),
        },
        timeout=60 * 5,  # 5 минут
    )
    return render(request, 'mailing/dashboard.html', context)

def statistics_report(request):
    """
    Собирает и отображает статистику по рассылкам и попыткам отправки.
    Обычный пользователь видит статистику только по своим рассылкам.
    Менеджер видит общую статистику по системе.
    """
    now = timezone.now()
    user = request.user

    # 1. Определяем, какой QuerySet использовать
    if is_manager(user):
        # Менеджер: видит всё
        mailings_qs = Mailing.objects.all()
        attempts_qs = MailingAttempt.objects.all()
    else:
        # Обычный пользователь: только свои рассылки и попытки
        mailings_qs = Mailing.objects.filter(owner=user)
        attempts_qs = MailingAttempt.objects.filter(mailing__owner=user)

    # 2. Общая статистика рассылок (уже отфильтрована по правам)
    total_mailings = mailings_qs.count()
    active_mailings = mailings_qs.filter(start_time__lte=now, end_time__gte=now).count()
    completed_mailings = mailings_qs.filter(end_time__lt=now).count()

    # 3. Агрегация попыток отправки
    stats = attempts_qs.aggregate(
        total_attempts=Count('id'),
        success_attempts=Count('id', filter=Q(status=MailingAttempt.STATUS_SUCCESS)),
        fail_attempts=Count('id', filter=Q(status=MailingAttempt.STATUS_FAIL))
    )

    total = stats['total_attempts'] or 0
    success = stats['success_attempts'] or 0

    # Расчёт процентов (защита от деления на ноль)
    success_rate = (success / total * 100) if total > 0 else 0.0
    fail_rate = 100.0 - success_rate

    # 4. Последние ошибки (тоже фильтруются по правам)
    recent_errors = attempts_qs.filter(
        status=MailingAttempt.STATUS_FAIL
    ).select_related('mailing', 'client').order_by('-sent_at')[:10]

    context = {
        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'completed_mailings': completed_mailings,

        'stats': stats,
        'recent_errors': recent_errors,

        # Готовые проценты для шаблона
        'success_rate': success_rate,
        'fail_rate': fail_rate,
    }

    return render(request, 'mailing/statistics_report.html', context)
Что важно проверить, чтобы это работало
Файл mixins.py должен существовать в папке mailing и содержать функцию is_manager:
python
# mailing/mixins.py
def is_manager(user):
    # Вариант с группой 'manager' (рекомендуется)
    return user.groups.filter(name='manager').exists()
    
    # Если хочешь использовать флаг is_staff вместо групп, раскомментируй строку ниже и закомментируй верхнюю:
    # return user.is_staff

def block_mailing(request, pk):
    if not is_manager(request.user):
        return HttpResponseForbidden("Доступ запрещен")
    
    mailing = get_object_or_404(Mailing, pk=pk)
    mailing.status = Mailing.STATUS_BLOCKED
    mailing.save()
    return redirect('mailing:mailing_list')
    
@login_required
@require_POST
def start_mailing(request, pk):
    # 1. Проверка прав (владелец)
    mailing = get_object_or_404(Mailing, pk=pk, owner=request.user)
    
    # 2. Ставим статус "Запущена" сразу, чтобы интерфейс обновился
    mailing.status = Mailing.STATUS_RUNNING
    mailing.save()

    # 3. Отправляем задачу в очередь Redis
    queue = django_rq.get_queue('default')
    job = queue.enqueue(run_mailing_task, mailing.id)

    messages.success(request, f"Рассылка #{mailing.id} отправлена в очередь обработки!")
    return redirect('mailing:dashboard')
