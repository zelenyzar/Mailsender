from django.urls import path
from django.contrib.auth.views import LogoutView
from user import views
from user.forms import CustomLoginForm

app_name = 'user'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    
    # Подтверждение email
    path('verify/<str:token>/', views.email_verification, name='verify'),
    
    # Сброс пароля
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
]
