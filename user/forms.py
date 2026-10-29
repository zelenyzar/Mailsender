from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from user.models import Users


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
        model = Users
        fields = ('email', 'password1', 'password2')


class EmailRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = Users
        fields = ('email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user
