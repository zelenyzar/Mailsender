import uuid
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.http import HttpResponseBadRequest

from user.forms import UserRegisterForm, CustomLoginForm, CustomPasswordResetForm, CustomSetPasswordForm
from user.models import User
from django.contrib.auth.tokens import default_token_generator

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Генерация токена
            token = str(uuid.uuid4())[:32]
            user.verification_token = token
            user.token_expires_at = timezone.now() + timedelta(hours=24)
            user.save()

            # Отправка письма
            subject = 'Подтверждение регистрации'
            message = render_to_string('user/email_verification.html', {
                'user': user,
                'token': token,
                'base_url': settings.BASE_URL,
            })
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
                html_message=message, # Если нужен HTML
            )

            messages.success(request, 'Регистрация успешна! Пожалуйста, проверьте почту для подтверждения аккаунта.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    
    return render(request, 'user/register.html', {'form': form})

def email_verification(request, token):
    try:
        user = get_object_or_404(User, verification_token=token)
        
        # Проверка срока действия
        if user.token_expires_at and user.token_expires_at < timezone.now():
            messages.error(request, 'Срок действия ссылки истек. Зарегистрируйтесь заново.')
            return redirect('register')

        # Активация
        user.is_active = True
        user.verification_token = None
        user.token_expires_at = None
        user.save()
        
        messages.success(request, 'Аккаунт успешно подтвержден! Теперь вы можете войти.')
        return redirect('login')
        
    except Exception:
        messages.error(request, 'Неверная ссылка подтверждения.')
        return redirect('home') # Или на главную

def custom_login(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(email=email, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    next_url = request.GET.get('next', '/')
                    return redirect(next_url)
                else:
                    messages.warning(request, 'Ваш аккаунт не подтвержден. Проверьте почту.')
                    return redirect('login')
            else:
                messages.error(request, 'Неверный логин или пароль.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'user/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('home')

# Логика сброса пароля
class CustomPasswordResetView(StyleFormMixin): # Можно сделать отдельным классом или функцией
    pass 

# Упрощенная реализация сброса пароля через функцию для наглядности
def password_reset_request(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            users = form.get_users(email)
            for user in users:
                # Генерируем токен и uid
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                subject = 'Сброс пароля'
                message = render_to_string('user/password_reset_email.html', {
                    'user': user,
                    'uid': uid,
                    'token': token,
                    'base_url': settings.BASE_URL,
                })
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)
            
            messages.success(request, 'Если такой пользователь существует, письмо со ссылкой на сброс пароля было отправлено.')
            return redirect('login')
    else:
        form = CustomPasswordResetForm()
    return render(request, 'user/password_reset.html', {'form': form})

def password_reset_confirm(request, uidb64, token):
    from django.utils.http import urlsafe_base64_decode
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Пароль успешно изменен! Вы можете войти в систему.')
                return redirect('login')
        else:
            form = CustomSetPasswordForm(user)
        return render(request, 'user/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'Ссылка для сброса пароля недействительна или устарела.')
        return redirect('password_reset')

def toggle_user_active(request, user_id):
    """
    Переключает статус is_active у пользователя.
    Доступно только менеджерам.
    """
    # 1. Проверка прав: только менеджер
    if not is_manager(request.user):
        return HttpResponseForbidden("У вас нет прав для управления пользователями.")

    # 2. Получаем пользователя
    target_user = get_object_or_404(User, pk=user_id)

    # Защита: менеджер не может заблокировать самого себя (опционально, но полезно)
    if target_user.id == request.user.id:
        messages.warning(request, "Вы не можете заблокировать сами себя.")
        return redirect('user:user_list')  # Замени на свой URL списка пользователей

    # 3. Переключаем статус
    target_user.is_active = not target_user.is_active
    target_user.save()

    # 4. Сообщение пользователю
    if target_user.is_active:
        msg = f"Пользователь {target_user.email} успешно разблокирован."
        level = messages.SUCCESS
    else:
        msg = f"Пользователь {target_user.email} заблокирован. Доступ к системе прекращен."
        level = messages.WARNING

    messages.add_message(request, level, msg)

    return redirect('user:user_list')
