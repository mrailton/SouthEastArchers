from django import forms
from .models import News


class NewsForm(forms.ModelForm):
    """Form for creating and editing news articles"""

    class Meta:
        model = News
        fields = ['title', 'content', 'published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'News title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'News content',
                'rows': 10
            }),
            'published': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
