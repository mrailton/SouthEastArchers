from django import forms
from .models import CreditPurchase


class CreditPurchaseForm(forms.Form):
    """Form for purchasing additional credits"""

    credits = forms.IntegerField(
        label='Number of Credits',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter number of credits to purchase',
            'min': '1'
        })
    )

    def __init__(self, *args, credit_cost=5, **kwargs):
        super().__init__(*args, **kwargs)
        self.credit_cost = credit_cost
