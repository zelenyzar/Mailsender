from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

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

            base_attrs = {
                "autocomplete": "off",  # можно оставить, но для password лучше new-password
            }

            if field_type == "file":
                widget.attrs.update({
                    **base_attrs,
                    "class": self.file_input_class,
                    "accept": "image/*",
                })
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({
                    **base_attrs,
                    "class": f"{self.base_control_class} rows=4",
                    "placeholder": "Введите текст",
                })
            elif isinstance(widget, forms.NumberInput):
                widget.attrs.update({
                    **base_attrs,
                    "class": f"{self.base_control_class} text-start",
                    "step": "1",
                    "min": "0",
                    "placeholder": "0",
                })
            elif isinstance(widget, forms.Select):
                widget.attrs.update({
                    **base_attrs,
                    "class": self.select_class,
                })
            else:
                widget.attrs.update({
                    **base_attrs,
                    "class": self.base_control_class,
                    "placeholder": "Введите значение",
                })

            placeholders = {
                "email": "your@example.com",
                "password1": "Придумайте надёжный пароль",
                "password2": "Повторите пароль",
            }
            if name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[name]

            if name in ("password1", "password2"):
                field.widget.attrs["autocomplete"] = "new-password"



class UserRegisterForm(StyleFormMixin,UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')


# НОВАЯ ФОРМА ДЛЯ ВХОДА
class CustomLoginForm(StyleFormMixin, AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'autofocus': True, 'class': 'form-control'})
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('username') # В стандартной форме поле называется username
        password = cleaned_data.get('password')
        
        if email and password:
            self.user_cache = Users.objects.filter(email=email).first()
            if not self.user_cache or not self.user_cache.check_password(password):
                raise forms.ValidationError("Неверный логин или пароль.")
            elif not self.user_cache.is_active:
                raise forms.ValidationError("Аккаунт не подтвержден. Проверьте почту.")
        return cleaned_data


# class EmailRegistrationForm(UserCreationForm):
#     email = forms.EmailField(required=True, label="Email")

#     class Meta:
#         model = User
#         fields = ('email', 'password1', 'password2')

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         if commit:
#             user.save()
#         return user
