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
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from user.forms import UserRegisterForm, CustomLoginForm, CustomPasswordResetForm, CustomSetPasswordForm
from user.models import User

# ---------------------------------------------------------
# РЕГИСТРАЦИЯ И ПОДТВЕРЖДЕНИЕ
# ---------------------------------------------------------

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Генерируем токен подтверждения
            token = str(uuid.uuid4())[:32]
            user.verification_token = token
            user.token_expires_at = timezone.now() + timedelta(hours=24)
            user.is_active = False  # Важно: сразу ставим неактивным
            user.save()

            # Отправляем письмо
            subject = 'Подтверждение регистрации в системе рассылок'
            message = render_to_string('user/email_verification.html', {
                'user': user,
                'token': token,
                'base_url': settings.BASE_URL,
            })
            
            try:
                send_mail(
                    subject,
                    "",  # text version (можно оставить пустым, если есть html_message)
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                    html_message=message,
                )
                messages.success(request, 'Регистрация успешна! Мы отправили письмо для подтверждения вашего email. Проверьте папку «Спам».')
                return redirect('login')
            except Exception as e:
                # Если почта не отправилась (нет SMTP, ошибка сети), удаляем пользователя или помечаем как ошибку
                user.delete()
                messages.error(request, f'Не удалось отправить письмо. Ошибка: {str(e)}')
                return redirect('register')
    else:
        form = UserRegisterForm()
    
    return render(request, 'user/register.html', {'form': form})

def email_verification(request, token):
    try:
        # Ищем пользователя по токену
        user = get_object_or_404(User, verification_token=token)
        
        # Проверка: не активирован ли уже?
        if user.is_active:
            messages.warning(request, 'Этот аккаунт уже подтвержден.')
            return redirect('login')

        # Проверка срока действия токена
        if user.token_expires_at and user.token_expires_at < timezone.now():
            messages.error(request, 'Срок действия ссылки истек. Пожалуйста, зарегистрируйтесь заново.')
            # Опционально: можно очистить старый токен и предложить кнопку "Отправить повторно"
            return redirect('register')

        # Активируем пользователя
        user.is_active = True
        user.verification_token = None
        user.token_expires_at = None
        user.save()
        
        messages.success(request, 'Аккаунт успешно подтвержден! Теперь вы можете войти в систему.')
        return redirect('login')
        
    except Exception:
        messages.error(request, 'Неверная или устаревшая ссылка подтверждения.')
        return redirect('home')

# ---------------------------------------------------------
# АВТОРИЗАЦИЯ И ВЫХОД
# ---------------------------------------------------------

def custom_login(request):
    # Если пользователь уже авторизован, перенаправляем его (опционально)
    if request.user.is_authenticated:
        return redirect('/') 

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            # Получаем email из формы. 
            # ВАЖНО: Убедись, что в CustomLoginForm поле называется 'email'. 
            # Если оно называется 'username', оставь как было.
            email = form.cleaned_data.get('email') or form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = authenticate(email=email, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    next_url = request.GET.get('next', '/')
                    return redirect(next_url)
                else:
                    messages.warning(request, 'Ваш аккаунт не подтвержден. Проверьте почту и перейдите по ссылке из письма.')
                    return redirect('login')
            else:
                messages.error(request, 'Неверный email или пароль.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'user/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('home') # Замени на свой URL главной страницы

# ---------------------------------------------------------
# СБРОС ПАРОЛЯ (FORGOT PASSWORD)
# ---------------------------------------------------------

def password_reset_request(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            users = form.get_users(email)
            
            sent_count = 0
            for user in users:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                subject = 'Сброс пароля для вашей учетной записи'
                message = render_to_string('user/password_reset_email.html', {
                    'user': user,
                    'uid': uid,
                    'token': token,
                    'base_url': settings.BASE_URL,
                })
                
                try:
                    send_mail(subject, "", settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True, html_message=message)
                    sent_count += 1
                except Exception as e:
                    messages.error(request, f"Не удалось отправить письмо на {email}. Ошибка: {e}")
            
            if sent_count > 0:
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
                messages.success(request, 'Пароль успешно изменен! Вы можете войти в систему с новым паролем.')
                return redirect('login')
        else:
            form = CustomSetPasswordForm(user)
        return render(request, 'user/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'Ссылка для сброса пароля недействительна или устарела.')
        return redirect('password_reset')

# ---------------------------------------------------------
# УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ (ДЛЯ МЕНЕДЖЕРОВ)
# ---------------------------------------------------------

# Вспомогательная функция проверки прав (замени на свою реальную логику)
def is_manager(user):
    # Пример: если у пользователя есть флаг is_manager в модели
    # return user.is_manager 
    # Или проверка группы: return user.groups.filter(name='manager').exists()
    # Для примера вернем False, чтобы не сломать код, если функции нет
    return getattr(user, 'is_manager', False) 

def toggle_user_active(request, user_id):
    """
    Переключает статус is_active у пользователя.
    Доступно только менеджерам.
    """
    if not is_manager(request.user):
        messages.error(request, "У вас нет прав для управления пользователями.")
        return redirect('home')

    target_user = get_object_or_404(User, pk=user_id)

    # Защита: менеджер не может заблокировать самого себя
    if target_user.id == request.user.id:
        messages.warning(request, "Вы не можете изменить статус собственного аккаунта.")
        return redirect('user:user_list')

    old_status = target_user.is_active
    target_user.is_active = not target_user.is_active
    target_user.save()

    if old_status:
        msg = f"Пользователь {target_user.email} заблокирован. Доступ к системе прекращен."
        level = messages.WARNING
    else:
        msg = f"Пользователь {target_user.email} успешно разблокирован."
        level = messages.SUCCESS

    messages.add_message(request, level, msg)
    return redirect('user:user_list')
