from django import forms
from .models import BACKEND_CHOICES


class NewPaymentForm(forms.Form):
    TIME_CHOICES = (
        ('1', '1'),
        ('3', '3'),
        ('6', '6'),
        ('12', '12'),
    )

    time = forms.ChoiceField(choices=TIME_CHOICES)
    method = forms.ChoiceField(choices=BACKEND_CHOICES)

