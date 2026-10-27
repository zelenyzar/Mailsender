from django.urls import path
from mailing.apps import MailingConfig
from mailing.views import home

app_name = MailingConfig.name

urlpatterns = [
  path('', home, name='home'),
]
