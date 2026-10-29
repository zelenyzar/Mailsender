from django import forms
from .models import Mailing
from django.utils import timezone

class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ('start_time', 'end_time', 'message', 'recipients')

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        now = timezone.now()

        if start_time and start_time < now:
            self.add_error('start_time', 'Дата начала не может быть в прошлом.')

        if start_time and end_time and start_time >= end_time:
            self.add_error(None, 'Дата начала должна быть раньше даты окончания.')

        return cleaned_data
