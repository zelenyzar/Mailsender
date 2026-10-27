from django.contrib import admin
from django.urls import path, include

urlpatterns = [
  path('admin/', adminsite.urls),
  path('', include('mailing.urls', namespace='mailing')),
]
