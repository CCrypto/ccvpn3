from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe


class FormPureRender:
    def as_pure_aligned(self):
        html = ''
        for f in self:
            html += '<div class="pure-control-group">\n'
            html += str(f.label_tag()) + '\n'
            html += str(f) + '\n'
            if f.errors:
                html += str(f.errors) + '\n'
            html += '</div>\n'
        return mark_safe(html)


class UserField(forms.RegexField):
    def clean(self, value):
        super(UserField, self).clean(value)
        try:
            User.objects.get(username=value)
            raise forms.ValidationError(_("Username taken."))
        except User.DoesNotExist:
            return value


class SignupForm(forms.Form, FormPureRender):
    username = UserField(
        label=_("Username"), min_length=2, max_length=16, regex='^[a-zA-Z0-9_-]+$',
        widget=forms.TextInput(attrs={'required': 'true',
                                      'pattern': '[a-zA-Z0-9_-]{2,32}',
                                      'placeholder': _("Username"),
                                      'autofocus': 'true'})
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'placeholder': _("Anything")})
    )
    password2 = forms.CharField(
        label=_("Repeat"),
        widget=forms.PasswordInput(attrs={'placeholder': _("Same Anything")})
    )
    email = forms.EmailField(
        label=_("E-Mail"),
        widget=forms.EmailInput(attrs={'placeholder': _("E-Mail")}),
        required=False,
    )

    def clean_password(self):
        if self.data['password'] != self.data['password2']:
            raise forms.ValidationError(_("Passwords are not the same"))
        return self.data['password']

