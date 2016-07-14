from django import forms
from .models import TicketMessage, CATEGORY_CHOICES
from django.utils.translation import ugettext_lazy as _


class NewTicketForm(forms.Form):
    category = forms.ChoiceField(label=_("Category"), choices=CATEGORY_CHOICES)
    subject = forms.CharField(label=_("Subject"), min_length=1, max_length=100)
    message = forms.CharField(label=_("Message"), widget=forms.Textarea)


class ReplyForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ('message',)


class StaffReplyForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ('message', 'staff_only')

    staff_only = forms.BooleanField(label=_("Private"), required=False)

