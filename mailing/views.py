from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from mailing.models import Client, Message

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
