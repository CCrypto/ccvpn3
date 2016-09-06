from django import forms
from .models import BACKEND_CHOICES


class NewPaymentForm(forms.Form):
    TIME_CHOICES = (
        ('1', '1'),
        ('3', '3'),
        ('6', '6'),
        ('12', '12'),
    )

    subscr = forms.ChoiceField(choices=(('0', 'no'), ('1', 'yes')))
    time = forms.ChoiceField(choices=TIME_CHOICES)
    method = forms.ChoiceField(choices=BACKEND_CHOICES)

