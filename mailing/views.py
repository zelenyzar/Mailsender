from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from mailing.models import Client, Message, Mailing

# --- Clients ---
class ClientListView(ListView):
  model = Client

class ClientDetailView(DetailView):
  model = Client

class ClientCreateView(CreateView):
  model = Client
  fields = ('email', 'full_name', 'comment')
  success_url = reverse-lazy('mailing:client_list')

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

  def get_object(sel, queryset=None):
    obj = super().get_object(queryset)
    obj.update_status() #пересчет и сохранение статуса при просмотре
    return obj

class MailingCreateView(CreateView):
  model = Mailing
  fields = ('start_time', 'end_time', 'message', 'recipients')
  success_url = reverse_lazy('mailing:mailing_list')

  def form_valid(self, form):
    response = super().form_valid(form)
    self.obj.update_status()
    return response

class MailingUpdateView(UpdateView):
  model = Mailing
  fields = ('start_time', 'end-time', 'message', recipients')
  success_url = reverse_lazy('mailing:mailing_list')

  def form_valid(self, form):
    response = super().form_valid(form)
    self.obj.update_status()
    return response

class MailingDeleteView(DeleteView):
  model = Mailing
  success_url = reverse_lazy('mailing:mailing_list')
