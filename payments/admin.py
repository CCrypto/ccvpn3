from django.shortcuts import resolve_url
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from .models import Payment, Subscription


def subscr_mark_as_cancelled(modeladmin, request, queryset):
    queryset.update(status='cancelled')
subscr_mark_as_cancelled.short_description = _("Mark as cancelled (do not actually cancel)")


class PaymentAdmin(admin.ModelAdmin):
    model = Payment
    list_display = ('user', 'backend', 'status', 'amount', 'paid_amount', 'created')
    list_filter = ('backend_id', 'status')

    fieldsets = (
        (None, {
            'fields': ('backend', 'user_link', 'subscription_link', 'time', 'status',
                       'status_message'),
        }),
        (_("Payment Data"), {
            'fields': ('amount_fmt', 'paid_amount_fmt',
                       'backend_extid_link', 'backend_data'),
        }),
    )

    readonly_fields = ('backend', 'user_link', 'time', 'status', 'status_message',
                       'amount_fmt', 'paid_amount_fmt', 'subscription_link',
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

    def subscription_link(self, object):
        change_url = resolve_url('admin:payments_subscription_change',
                                 object.subscription.id)
        return '<a href="%s">%s</a>' % (change_url, object.subscription.id)
    subscription_link.allow_tags = True
    subscription_link.short_description = 'Subscription'


class SubscriptionAdmin(admin.ModelAdmin):
    model = Subscription
    list_display = ('user', 'created', 'status', 'backend', 'backend_extid')
    readonly_fields = ('user_link', 'backend', 'period', 'created', 'status',
                       'last_confirmed_payment', 'payments_links',
                       'backend_extid_link', 'backend_data')
    actions = (subscr_mark_as_cancelled,)
    fieldsets = (
        (None, {
            'fields': ('backend', 'user_link', 'period', 'payments_links', 'status',
                       'last_confirmed_payment'),
        }),
        (_("Payment Data"), {
            'fields': ('backend_extid_link', 'backend_data'),
        }),
    )

    def backend(self, object):
        return object.backend.backend_verbose_name

    def user_link(self, object):
        change_url = resolve_url('admin:auth_user_change', object.user.id)
        return '<a href="%s">%s</a>' % (change_url, object.user.username)
    user_link.allow_tags = True
    user_link.short_description = 'User'

    def payments_links(self, object):
        fmt = '<a href="%s?subscription__id__exact=%d">%d payments</a>'
        payments_url = resolve_url('admin:payments_payment_changelist')
        count = Payment.objects.filter(subscription=object).count()
        return fmt % (payments_url, object.id, count)
    payments_links.allow_tags = True
    payments_links.short_description = 'Payments'

    def backend_extid_link(self, object):
        ext_url = object.backend.get_subscr_ext_url(object)
        if ext_url:
            return '<a href="%s">%s</a>' % (ext_url, object.backend_extid)
        return object.backend_extid
    backend_extid_link.allow_tags = True

admin.site.register(Payment, PaymentAdmin)
admin.site.register(Subscription, SubscriptionAdmin)

