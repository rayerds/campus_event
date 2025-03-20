from django import forms
from django.contrib.auth.models import User
from .models import Event

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

class EventForm(forms.ModelForm):
    sync_to_calendar = forms.BooleanField(required=False, initial=True, label='Sync to Google Calendar?')

    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'time', 'location']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }