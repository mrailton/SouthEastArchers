from django import forms
from .models import ShootingNight


class ShootingNightForm(forms.ModelForm):
    """Form for creating and editing shooting nights"""

    attendees = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set in the view
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = ShootingNight
        fields = ['date', 'location', 'notes', 'attendees']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'location': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Additional notes',
                'rows': 4
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Queryset will be set dynamically in the view
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['attendees'].queryset = User.objects.filter(is_active=True)
