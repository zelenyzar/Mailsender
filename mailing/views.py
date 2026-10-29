from django.contrib.messages import success
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .forms import MailingForm

from mailing.models import Client, Message, Mailing, MailingAttempt


# --- Clients ---
class ClientListView(ListView):
    model = Client


class ClientDetailView(DetailView):
    model = Client


class ClientCreateView(CreateView):
    model = Client
    fields = ('email', 'full_name', 'comment')
    success_url = reverse_lazy('mailing:client_list')


class ClientUpdateView(UpdateView):
    model = Client
    fields = ('email', 'full_name', 'comment')
    success_url = reverse_lazy('mailing:client_list')


class ClientDeleteView(DeleteView):
    model = Client
    success_url = reverse_lazy('mailing:client_list')


# --- Message ---
class MessageListView(ListView):
    model = Message


class MessageDetailView(DetailView):
    model = Message


class MessageCreateView(CreateView):
    model = Message
    fields = ('subject', 'message')
    success_url = reverse_lazy('mailing:message_list')


class MessageUpdateView(UpdateView):
    model = Message
    fields = ('subject', 'message')
    success_url = reverse_lazy('mailing:message_list')


class MessageDeleteView(DeleteView):
    model = Message
    success_url = reverse_lazy('mailing:message_list')


# --- Mailing ---
class MailingListView(ListView):
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
    success_url = reverse_lazy('mailing:mailing_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.update_status()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages_list'] = Message.objects.all()
        context['clients_list'] = Client.objects.all()
        context['recipient_ids'] = []
        return context


class MailingUpdateView(UpdateView):
    model = Mailing
    form_class = MailingForm
    success_url = reverse_lazy('mailing:mailing_list')

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


class MailingDeleteView(DeleteView):
    model = Mailing
    success_url = reverse_lazy('mailing:mailing_list')


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
    total_mailings = Mailing.objects.count()
    unique_recipients = Client.objects.count()
    active_mailings = Mailing.objects.filter(
        start_time__lte=now,
        end_time__gte=now
    ).count()
    context = {
        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'unique_recipients': unique_recipients,
    }
    return render(request, 'mailing/dashboard.html', context)
