from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth.views import LogoutView
from django.urls import path
from user.apps import UserConfig
from user.views import UserCreateView, email_verification, CustomPasswordResetView, CustomPasswordResetConfirmView, CustomPasswordResetCompleteView
from user.forms import CustomLoginForm # Импортируем нашу форму
from django.contrib.auth.views import LoginView

app_name = UserConfig.name

urlpatterns = [
    # Используем нашу форму для входа
    path('login/', LoginView.as_view(template_name='user/login.html', authentication_form=CustomLoginForm), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', UserCreateView.as_view(), name='register'),
    path('email-confirm/<str:token>/', email_verification, name='email_confirm'),
    
    # Сброс пароля
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='user/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
