import secrets

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView

from user.forms import UserRegisterForm
from user.models import Users

from config.settings import EMAIL_HOST_USER


class UserCreateView(CreateView):
    model = Users
    form_class = UserRegisterForm
    template_name = 'user/user_form.html'
    success_url = reverse_lazy('user:login')

    def form_valid(self, form):
        user = form.save()
        user.is_active = False
        token = secrets.token_hex(16)
        user.token = token
        user.save()

        host = self.request.get_host()
        protocol = 'https' if self.request.is_secure() else 'http'
        url = f'{protocol}://{host}/user/email-confirm/{token}/'

        try:
            send_mail(
                subject='Добро пожаловать в наш проект!',
                message=(
                    f'Привет!\n\n'
                    'Спасибо, что зарегистрировался!\n\n'
                    'Твой аккаунт пока не активен - нужно подтвердить почту по ссылке из следующего письма.\n\n'
                    'До встречи внутри!'
                ),
                from_email=EMAIL_HOST_USER,
                recipient_list=[user.email],
            )
        except Exception as e:
            print(f"Warning: failed to send welcome email to {user.email}: {e}")

        try:
            send_mail(
                subject='Подтверждение почты',
                message=(
                    f'Привет!\n\n'
                    f'Чтобы активировать аккаунт, перейди по ссылке:\n{url}\n\n'
                    'Если ты не регистрировался - просто проигнорируй это письмо.'
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
            )
        except Exception as e:
            print(f"[Confirm Email Error] {e}")
            # Если не ушло подтверждение - откатываем регистрацию
            user.delete()
            messages.error(self.request, 'Не удалось отправить письмо с подтверждением. Пожалуйста, попробуйте позже.')
            return redirect('user:register')

        messages.success(self.request, 'Регистрация прошла успешно! Проверьте почту для подтверждения.')

        return super().form_valid(form)

def email_verification(request, token):
    user = get_object_or_404(Users, token=token)

    if user.is_active:
        messages.info(request, 'Этот аккаунт уже подтверждён.')
        return redirect('user:login')

    user.is_active=True
    user.token = ''
    user.save()

    messages.success(request, 'Почта подтверждена! Теперь можно войти.')

    return redirect('user:login')
