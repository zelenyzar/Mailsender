from django.urls import path
from mailing.apps import MailingConfig
from .views import (
  ClientListView,
  ClientDetailView,
  ClientCreateView,
  ClientUpdateView,
  ClientDeleteView,
  MessageListView,
  MessageDetailView, 
  MessageCreateView,
  MessageUpdateView,
  MessageDeleteView
)

app_name = MailingConfig.name

urlpatterns = [
  path('', ClientListView.as_view(), name='client_list'),
  path('mailing/<int:pk>/', ClientDetailView.as_view(), name='client_detail'),
  path('mailing/create', ClientCreateView.as_view(), name='client_create'),
  path('mailing/<int:pk>/update', ClientUpdateView.as_view(), name='client_update'),
  path('mailing/<int:pk>/delete', ClientDeleteView.as_view(), name='client_delete'),

  path('', MessageListView.as_view(), name='message_list'),
  path('mailing/<int:pk>/', MessageDetailView.as_view(), name='message_detail'),
  path('mailing/create', MessageCreateView.as_view(), name='message_create'),
  path('mailing/<int:pk>/update', MessageUpdateView.as_view(), name='message_update'),
  path('mailing/<int:pk>/delete', MessageDeleteView.as_view(), name='message_delete'),
]
