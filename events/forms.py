from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    """Form for creating and editing events"""

    class Meta:
        model = Event
        fields = ['title', 'description', 'event_date', 'location', 'published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Event description',
                'rows': 6
            }),
            'event_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event location'
            }),
            'published': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
