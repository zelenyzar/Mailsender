from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
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
                # rows=4 лучше задавать через атрибут, а не в классе
                widget.attrs.update({**base_attrs, "class": f"{self.base_control_class}", "rows": "4"})
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
            user.is_active = False
            user.save()
        return user

# --- ИСПРАВЛЕННАЯ ФОРМА ВХОДА ---
class CustomLoginForm(StyleFormMixin, AuthenticationForm):
    # Используем отдельное поле email вместо переопределения username
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'autofocus': True}))
    password = forms.CharField(label="Пароль", strip=False, widget=forms.PasswordInput())

    error_messages = {
        'invalid_login': "Неверный email или пароль.",
        'inactive': "Аккаунт не подтвержден. Проверьте почту.",
    }

    # Переопределяем clean(), чтобы использовать наше поле email для аутентификации
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

# Форма сброса пароля
class CustomPasswordResetForm(StyleFormMixin, PasswordResetForm):
    email = forms.EmailField(label='Email', max_length=254)

    def get_users(self, email):
        active_users = User._default_manager.filter(
            email__iexact=email,
            is_active=True
        )
        return active_users

# Форма установки нового пароля
class CustomSetPasswordForm(StyleFormMixin, SetPasswordForm):
    pass
