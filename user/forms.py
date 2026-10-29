from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from user.models import User

class StyleFormMixin:
    base_control_class = "form-control shadow-sm"
    select_class = "form-select"
    file_input_class = "form-control"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()

    def _apply_styles(self):
        for name, field in self.fields.items():
            widget = field.widget
            field_type = widget.input_type

            base_attrs = {"autocomplete": "off"}

            if field_type == "file":
                widget.attrs.update({**base_attrs, "class": self.file_input_class, "accept": "image/*"})
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({**base_attrs, "class": f"{self.base_control_class} rows=4"})
            elif isinstance(widget, forms.NumberInput):
                widget.attrs.update({**base_attrs, "class": f"{self.base_control_class} text-start", "step": "1", "min": "0"})
            elif isinstance(widget, forms.Select):
                widget.attrs.update({**base_attrs, "class": self.select_class})
            else:
                widget.attrs.update({**base_attrs, "class": self.base_control_class})

            placeholders = {
                "email": "your@example.com",
                "password1": "Придумайте надёжный пароль",
                "password2": "Повторите пароль",
                "new_password1": "Новый пароль",
                "new_password2": "Повторите новый пароль",
            }
            if name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[name]

            if name in ("password1", "password2", "new_password1", "new_password2"):
                field.widget.attrs["autocomplete"] = "new-password"

# Форма регистрации
class UserRegisterForm(StyleFormMixin, UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.is_active = False  # Деактивируем до подтверждения почты
            user.save()
        return user

# Форма входа (переопределяем поле username на email)
class CustomLoginForm(StyleFormMixin, AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'autofocus': True}))
    password = forms.CharField(label="Пароль", strip=False, widget=forms.PasswordInput())

    error_messages = {
        'invalid_login': "Неверный логин или пароль.",
        'inactive': "Аккаунт не подтвержден. Проверьте почту.",
    }

# Форма сброса пароля (стандартная, но с кастомным поиском по email)
class CustomPasswordResetForm(StyleFormMixin, PasswordResetForm):
    email = forms.EmailField(label='Email', max_length=254)

    def get_users(self, email):
        """Возвращает активных пользователей с указанным email."""
        active_users = User._default_manager.filter(
            email__iexact=email,
            is_active=True
        )
        return active_users

# Форма установки нового пароля
class CustomSetPasswordForm(StyleFormMixin, SetPasswordForm):
    pass
