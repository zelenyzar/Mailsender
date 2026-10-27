from django.urls import path
from mailing.apps import MailingConfig
from mailing.views import ClientListView, ClientDetailView, ClientCreateView, ClientUpdateView, ClientDeleteView

app_name = MailingConfig.name

urlpatterns = [
  path('', ClientListView.as_view(), name='client_list'),
  path('mailing/<int:pk>/', ClientDetailView.as_view(), name='client_detail'),
  path('mailing/create', ClientCreateView.as_view(), name='client_create'),
  path('mailing/<int:pk>/update', ClientUpdateView.as_view(), name='client_update'),
  path('mailing/<int:pk>/delete', ClientDeleteView.as_view(), name='client_delete')
]
