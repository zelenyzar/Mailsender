from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .forms import MailingForm, ClientForm, MessageForm
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import django_rq
from django.core.cache import cache

from .mixins import OwnerCheckMixin, OwnerOrManagerMixin
from .permissions import is_manager
from .tasks import run_mailing_task

from mailing.models import Client, Message, Mailing, MailingAttempt


# --- Clients ---
class ClientListView(OwnerOrManagerMixin, ListView):
    model = Client


class ClientDetailView(LoginRequiredMixin, OwnerOrManagerMixin, DetailView):
    model = Client


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        cache.clear()
        return response


class ClientUpdateView(OwnerCheckMixin, UpdateView):
    model = Client
    form_class = ClientForm

    def form_valid(self, form):
        response = super().form_valid(form)
        cache.clear()
        return response


class ClientDeleteView(OwnerCheckMixin, DeleteView):
    model = Client
    template_name = 'mailing/includes/confirm_delete.html'
    success_url = '/clients/'

    def form_valid(self, form):
        response = super().form_valid(form)
        cache.clear()
        return response

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
class MessageListView(OwnerOrManagerMixin, ListView):
    model = Message


class MessageDetailView(OwnerOrManagerMixin, DetailView):
    model = Message


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    success_url = reverse_lazy('mailing:message_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(OwnerCheckMixin, UpdateView):
    model = Message
    form_class = MessageForm
    success_url = reverse_lazy('mailing:message_list')


class MessageDeleteView(OwnerCheckMixin, DeleteView):
    model = Message
    template_name = 'mailing/includes/confirm_delete.html'
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

    def get_queryset(self):
        Mailing.update_all_statuses()
        return super().get_queryset().select_related('message', 'owner')


class MailingDetailView(OwnerOrManagerMixin, DetailView):
    model = Mailing

    def get_queryset(self):
        return super().get_queryset().prefetch_related('attempts')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
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


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['message'].queryset = Message.objects.filter(owner=self.request.user)
        form.fields['recipients'].queryset = Client.objects.filter(owner=self.request.user)
        return form

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        cache.clear()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages_list'] = Message.objects.filter(owner=self.request.user)
        context['clients_list'] = Client.objects.filter(owner=self.request.user)
        context['recipient_ids'] = []
        return context


class MailingUpdateView(OwnerCheckMixin, UpdateView):
    model = Mailing
    form_class = MailingForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['message'].queryset = Message.objects.filter(owner=self.request.user)
        form.fields['recipients'].queryset = Client.objects.filter(owner=self.request.user)
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.update_status()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages_list'] = Message.objects.filter(owner=self.request.user)
        context['clients_list'] = Client.objects.filter(owner=self.request.user)

        if self.object:
            context['recipient_ids'] = list(self.object.recipients.values_list('id', flat=True))
        else:
            context['recipient_ids'] = []
        return context


class MailingDeleteView(OwnerCheckMixin, DeleteView):
    model = Mailing
    template_name = 'mailing/includes/confirm_delete.html'
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

@login_required
@require_POST
def mailing_send(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)

    if mailing.owner_id != request.user.pk:
        return HttpResponseForbidden("Доступ запрещен")

    success, errors = mailing.send()
    mailing.update_status()

    cache.delete('statistics_global')
    if mailing.owner_id:
        cache.delete(f'statistics_user_{mailing.owner_id}')
        cache.delete(f'mailing_list_{mailing.owner_id}')
        cache.delete(f'dashboard_{mailing.owner_id}')
    cache.delete('mailing_list_all')

    if success:
        messages.success(request, f'Рассылка #{mailing.pk} успешно отправлена всем получателям!')
    else:
        error_text = '\n'.join(errors)
        messages.error(request, f'Частичная ошибка при отправке рассылки #{mailing.pk}:\n{error_text}')
    return redirect('mailing:mailing_detail', pk=mailing.pk)


# --- Dashboard ---
@login_required
def dashboard(request):
    Mailing.update_all_statuses()
    now = timezone.now()

    # Менеджер видит всю статистику, обычный пользователь — только свою
    if is_manager(request.user):
        mailings_qs = Mailing.objects.all()
        clients_qs = Client.objects.all()
    else:
        mailings_qs = Mailing.objects.filter(owner=request.user)
        clients_qs = Client.objects.filter(owner=request.user)

    context = cache.get_or_set(
        f'dashboard_{request.user.pk}',
        lambda: {
            'total_mailings': mailings_qs.count(),
            'unique_recipients': clients_qs.count(),
            'active_mailings': mailings_qs.filter(
                status=Mailing.STATUS_RUNNING,
                start_time__lte=now,
                end_time__gte=now
            ).count(),
        },
        timeout=60,
    )

    context['last_mailings'] = (
        mailings_qs
        .select_related('message')
        .order_by('-start_time')[:5]
    )

    return render(request, 'mailing/dashboard.html', context)

@login_required
def statistics_report(request):
    now = timezone.now()
    user = request.user

    if is_manager(user):
        mailings_qs = Mailing.objects.all()
        attempts_qs = MailingAttempt.objects.all()
        scope_label = 'Общая статистика по всем пользователям'
    else:
        mailings_qs = Mailing.objects.filter(owner=user)
        attempts_qs = MailingAttempt.objects.filter(mailing__owner=user)
        scope_label = 'Моя статистика'

    total_mailings = mailings_qs.count()
    active_mailings = mailings_qs.filter(
        status=Mailing.STATUS_RUNNING,
        start_time__lte=now,
        end_time__gte=now,
    ).count()
    completed_mailings = mailings_qs.filter(status=Mailing.STATUS_COMPLETED).count()

    stats = attempts_qs.aggregate(
        total_attempts=Count('id'),
        messages_sent=Count('id', filter=Q(status=MailingAttempt.STATUS_SUCCESS)),
        messages_failed=Count('id', filter=Q(status=MailingAttempt.STATUS_FAIL)),
        unique_recipients=Count('client', distinct=True),
    )

    total = stats['total_attempts'] or 0
    success = stats['messages_sent'] or 0
    success_rate = (success / total * 100) if total > 0 else 0.0
    fail_rate = 100.0 - success_rate

    recent_errors = (
        attempts_qs.filter(status=MailingAttempt.STATUS_FAIL)
        .select_related('mailing', 'client')
        .order_by('-sent_at')[:10]
    )

    users_stats = None
    if is_manager(user):
        users_stats = (
            Mailing.objects
            .values('owner__email')
            .annotate(
                mailings=Count('id', distinct=True),
                total=Count('attempts'),
                sent=Count('attempts', filter=Q(attempts__status=MailingAttempt.STATUS_SUCCESS)),
                failed=Count('attempts', filter=Q(attempts__status=MailingAttempt.STATUS_FAIL)),
            )
            .order_by('-total')
        )

    context = {
        'scope_label': scope_label,
        'is_manager': is_manager(user),

        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'completed_mailings': completed_mailings,

        'stats': stats,
        'recent_errors': recent_errors,
        'users_stats': users_stats,

        'success_rate': success_rate,
        'fail_rate': fail_rate,
    }

    return render(request, 'mailing/statistics_report.html', context)

@login_required
@require_POST
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
    mailing = get_object_or_404(Mailing, pk=pk, owner=request.user)

    mailing.status = Mailing.STATUS_RUNNING
    mailing.save()

    queue = django_rq.get_queue('default')
    job = queue.enqueue(run_mailing_task, mailing.id)

    messages.success(request, f"Рассылка #{mailing.id} отправлена в очередь обработки!")
    return redirect('mailing:dashboard')
