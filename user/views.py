import secrets
import string
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import CreateView, View
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView

from user.forms import UserRegisterForm
from user.models import Users


class UserCreateView(CreateView):
    model = Users
    form_class = UserRegisterForm
    template_name = 'user/user_form.html'
    success_url = reverse_lazy('user:login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False  # Пользователь не активен до подтверждения почты
        
        # Генерация токена
        token = secrets.token_urlsafe(32)
        user.token = token
        user.save()

        # Отправка письма
        subject = "Подтверждение регистрации"
        message = f"Здравствуйте! Для подтверждения регистрации перейдите по ссылке:\n\n{settings.BASE_URL}/user/email-confirm/{token}/\n\nЕсли вы не регистрировались, просто проигнорируйте это письмо."
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]

        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            messages.success(self.request, "Регистрация успешна! Проверьте почту для подтверждения.")
        except Exception as e:
            # В продакшене лучше логировать ошибку, а пользователю показать сообщение об ошибке
            messages.error(self.request, f"Не удалось отправить письмо: {str(e)}")
            user.delete() # Отменяем регистрацию при ошибке отправки
            return redirect('user:register')

        return super().form_valid(form)


def email_verification(request, token):
    """Обработка перехода по ссылке подтверждения"""
    user = get_object_or_404(Users, token=token)
    
    # Проверка срока действия токена (опционально, например, 24 часа)
    if user.date_joined + timedelta(hours=24) < timezone.now():
        messages.error(request, "Срок действия ссылки истек. Пожалуйста, зарегистрируйтесь заново.")
        return redirect('user:register')

    user.is_active = True
    user.token = None # Очищаем токен после использования
    user.save()
    messages.success(request, "Email подтвержден! Теперь вы можете войти в систему.")
    return redirect('user:login')


# --- Логика восстановления пароля ---

class CustomPasswordResetView(PasswordResetView):
    """Переопределяем стандартный вид сброса пароля, чтобы использовать email вместо username"""
    email_template_name = 'user/password_reset_email.html'
    subject_template_name = 'user/password_reset_subject.txt'
    template_name = 'user/password_reset_form.html'
    success_url = reverse_lazy('user:password_reset_done')
    
    # Важно: так как у нас USERNAME_FIELD = 'email', стандартная форма может не подойти.
    # Но PasswordResetView по умолчанию ищет по полю username. 
    # Нам нужно подменить форму, чтобы она искала по email.
    from django.contrib.auth.forms import PasswordResetForm
    
    class EmailBasedPasswordResetForm(PasswordResetForm):
        def get_users(self, email):
            """Возвращает пользователей с указанным email"""
            return Users.objects.filter(email__iexact=email, is_active=True)

    form_class = EmailBasedPasswordResetForm


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'user/password_reset_confirm.html'
    success_url = reverse_lazy('user:password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'user/password_reset_complete.html'
