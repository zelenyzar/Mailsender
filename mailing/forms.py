from django import forms
from .models import Client, Message, Mailing
from django.utils import timezone

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ('email', 'full_name', 'comment')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('subject', 'message')
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }

class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ('start_time', 'end_time', 'message', 'recipients')

    def clean(self):
    cleaned_data = super().clean()
    start_time = cleaned_data.get('start_time')
    end_time = cleaned_data.get('end_time')
    now = timezone.now()

    # Для новой рассылки (или если дату поменяли) запрещаем прошлое
    if start_time and start_time < now:
        if self.instance and self.instance.pk and self.instance.start_time == start_time:
            pass  # дату не меняли — не ругаемся
        else:
            self.add_error('start_time', 'Дата начала не может быть в прошлом.')

    if start_time and end_time and start_time >= end_time:
        self.add_error(None, 'Дата начала должна быть раньше даты окончания.')

    return cleaned_data
