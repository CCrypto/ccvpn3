from django.contrib import admin
from django.shortcuts import resolve_url
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils import formats
from .models import Ticket, TicketMessage, TicketNotifyAddress


def close_without_notice(modeladmin, request, queryset):
    queryset.update(is_open=False, closed=timezone.now())
close_without_notice.short_description = _("Close selected tickets (without notice)")


def close_tickets(modeladmin, request, queryset):
    for t in queryset:
        if t.is_open:
            t.notify_close()
    queryset.update(is_open=False, closed=timezone.now())
close_tickets.short_description = _("Close selected tickets")


class TicketMessageAdmin(admin.StackedInline):
    model = TicketMessage
    fields = ('user_link', 'remote_addr', 'created', 'staff_only', 'message')
    readonly_fields = ('user_link', 'created')
    extra = 1

    def user_link(self, object):
        change_url = resolve_url('admin:auth_user_change', object.user.id)
        return '<a href="%s">%s</a>' % (change_url, object.user.username)
    user_link.allow_tags = True
    user_link.short_description = 'User'


class TicketAdmin(admin.ModelAdmin):
    fields = ('category', 'subject', 'user_link', 'created', 'status', 'closed')
    readonly_fields = ('user_link', 'created', 'status', 'closed')
    list_display = ('subject', 'user', 'created', 'category', 'is_open')
    list_filter = ('category', 'is_open')
    search_fields = ('subject', 'user__username', 'message_set__message')
    actions = (close_tickets, close_without_notice)
    inlines = (TicketMessageAdmin,)

    def user_link(self, object):
        change_url = resolve_url('admin:auth_user_change', object.user.id)
        return '<a href="%s">%s</a>' % (change_url, object.user.username)
    user_link.allow_tags = True
    user_link.short_description = 'User'

    def comment_head(self, object):
        return object.comment_head
    comment_head.short_description = _("Comment")

    def status(self, object):
        if object.is_open and object.closed:
            return _("Re-opened")
        elif object.is_open:
            return _("Open")
        else:
            return _("Closed")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        obj.save()

    def save_formset(self, request, form, formset, change):
        formset.save()
        if not change:
            for f in formset.forms:
                obj = f.instance
                obj.user = request.user
                obj.save()


class TicketNotifyAddressAdmin(admin.ModelAdmin):
    list_display = ('category', 'address')
    list_filter = ('category', )
    search_fields = ('address', )


admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketNotifyAddress, TicketNotifyAddressAdmin)

