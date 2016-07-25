import string
from django.shortcuts import resolve_url
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from lambdainst.models import VPNUser, GiftCode, GiftCodeUser
from . import core

def make_user_link(user):
    change_url = resolve_url('admin:auth_user_change', user.id)
    return '<a href="%s">%s</a>' % (change_url, user.username)


class GiftCodeAdminForm(forms.ModelForm):
    def clean(self):
        input_code = self.cleaned_data.get('code', '')
        code_charset = string.ascii_letters + string.digits
        if any(c not in code_charset for c in input_code):
            raise forms.ValidationError(_("Code must be [a-zA-Z0-9]"))
        if not 1 <= len(input_code) <= 32:
            raise forms.ValidationError(_("Code must be between 1 and 32 characters"))
        return self.cleaned_data


class VPNUserInline(admin.StackedInline):
    model = VPNUser
    can_delete = False
    fk_name = 'user'

    fields = ('notes', 'expiration', 'last_expiry_notice', 'notify_expiration',
              'trial_periods_given', 'referrer_a', 'last_vpn_auth')
    readonly_fields = ('referrer_a', 'last_vpn_auth')

    def referrer_a(self, object):
        if not object.referrer:
            return "-"

        s = make_user_link(object.referrer) + " "
        if object.referrer_used:
            s += _("(rewarded)")
        else:
            s += _("(not rewarded)")
        return s
    referrer_a.allow_tags = True
    referrer_a.short_description = _("Referrer")

    def is_paid(self, object):
        return object.is_paid
    is_paid.boolean = True
    is_paid.short_description = _("Is paid?")


class GiftCodeUserAdmin(admin.TabularInline):
    model = GiftCodeUser
    fields = ('user_link', 'code_link', 'date')
    readonly_fields = ('user_link', 'code_link', 'date')
    list_display = ('user', )
    original = False

    def user_link(self, object):
        return make_user_link(object.user)
    user_link.allow_tags = True
    user_link.short_description = 'User'

    def code_link(self, object):
        change_url = resolve_url('admin:lambdainst_giftcode_change', object.code.id)
        return '<a href="%s">%s</a>' % (change_url, object.code.code)
    code_link.allow_tags = True
    code_link.short_description = 'Code'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class UserAdmin(UserAdmin):
    inlines = (VPNUserInline, GiftCodeUserAdmin)
    list_display = ('username', 'email', 'is_staff', 'date_joined', 'is_paid')
    ordering = ('-date_joined', )
    fieldsets = (
        (None, {'fields': ('username', 'password', 'email', 'links')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
    )
    readonly_fields = ('last_login', 'date_joined', 'links')

    def is_paid(self, object):
        return object.vpnuser.is_paid
    is_paid.boolean = True
    is_paid.short_description = _("Is paid?")

    def links(self, object):
        fmt = '<a href="%s?user__id__exact=%d">%s</a>'
        payments_url = resolve_url('admin:payments_payment_changelist')
        tickets_url = resolve_url('admin:tickets_ticket_changelist')
        s = fmt % (payments_url, object.id, "Payments")
        s += ' - ' + fmt % (tickets_url, object.id, "Tickets")
        return s
    links.allow_tags = True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Notify core
        if change and core.VPN_AUTH_STORAGE == 'core':
            core.update_user_expiration(obj)

    def delete_model(self, request, obj):
        if core.VPN_AUTH_STORAGE == 'core':
            core.delete_user(obj.username)

        super().delete_model(request, obj)


class GiftCodeAdmin(admin.ModelAdmin):
    fields = ('code', 'time', 'created', 'created_by', 'single_use', 'free_only',
              'available', 'comment')
    readonly_fields = ('created', 'created_by')
    list_display = ('code', 'time', 'comment_head', 'available')
    search_fields = ('code', 'comment', 'users__username')
    inlines = (GiftCodeUserAdmin,)
    list_filter = ('available', 'time')
    form = GiftCodeAdminForm

    def comment_head(self, object):
        return object.comment_head
    comment_head.short_description = _("Comment")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.save()


admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(GiftCode, GiftCodeAdmin)

