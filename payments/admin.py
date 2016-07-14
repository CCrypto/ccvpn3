from django.shortcuts import resolve_url
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from .models import Payment, RecurringPaymentSource


class PaymentAdmin(admin.ModelAdmin):
    model = Payment
    list_display = ('user', 'backend', 'status', 'amount', 'paid_amount', 'created')
    list_filter = ('backend_id', 'status')

    fieldsets = (
        (None, {
            'fields': ('backend', 'user_link', 'time', 'status', 'status_message'),
        }),
        (_("Payment Data"), {
            'fields': ('amount_fmt', 'paid_amount_fmt', 'recurring_source',
                       'backend_extid_link', 'backend_data'),
        }),
    )

    readonly_fields = ('backend', 'user_link', 'time', 'status', 'status_message',
                       'amount_fmt', 'paid_amount_fmt', 'recurring_source',
                       'backend_extid_link', 'backend_data')
    search_fields = ('user__username', 'user__email', 'backend_extid', 'backend_data')

    def backend(self, object):
        return object.backend.backend_verbose_name

    def backend_extid_link(self, object):
        ext_url = object.backend.get_ext_url(object)
        if ext_url:
            return '<a href="%s">%s</a>' % (ext_url, object.backend_extid)
        return object.backend_extid
    backend_extid_link.allow_tags = True

    def amount_fmt(self, object):
        return '%.2f %s' % (object.amount / 100, object.currency_name)
    amount_fmt.short_description = _("Amount")

    def paid_amount_fmt(self, object):
        return '%.2f %s' % (object.paid_amount / 100, object.currency_name)
    paid_amount_fmt.short_description = _("Paid amount")

    def user_link(self, object):
        change_url = resolve_url('admin:auth_user_change', object.user.id)
        return '<a href="%s">%s</a>' % (change_url, object.user.username)
    user_link.allow_tags = True
    user_link.short_description = 'User'


class RecurringPaymentSourceAdmin(admin.ModelAdmin):
    model = RecurringPaymentSource
    list_display = ('user', 'backend', 'created')
    readonly_fields = ('user', 'backend', 'created', 'last_confirmed_payment')


admin.site.register(Payment, PaymentAdmin)
admin.site.register(RecurringPaymentSource, RecurringPaymentSourceAdmin)

