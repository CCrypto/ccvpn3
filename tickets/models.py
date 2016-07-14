from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.template.loader import get_template
from django.template import Context
from django.core.mail import send_mail


ROOT_URL = settings.ROOT_URL
SITE_NAME = settings.TICKETS_SITE_NAME

CATEGORY_CHOICES = (
    ('support', _("Support")),
    ('security', _("Security")),
    ('billing', _("Account / Billing")),
)

if hasattr(settings, 'TICKETS_CATEGORIES'):
    CATEGORY_CHOICES = settings.TICKETS_CATEGORIES


def notify(subject, template, recipient_list, params):
    ctx = Context(dict(site_name=SITE_NAME, **params))
    text = get_template(template).render(ctx)

    for a in recipient_list:
        send_mail(subject, text, settings.DEFAULT_FROM_EMAIL, [a], fail_silently=True)


class Ticket(models.Model):
    class Meta:
        ordering = ('-created',)

        permissions = (
            ('view_any_ticket', _("Can view any ticket")),
            ('reply_any_ticket', _("Can reply to any ticket")),
            ('view_private_message', _("Can view private messages on tickets")),
            ('post_private_message', _("Can post private messages on tickets")),
        )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                             on_delete=models.SET_NULL)
    category = models.CharField(max_length=16, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    is_open = models.BooleanField(default=True)
    closed = models.DateTimeField(blank=True, null=True)

    @property
    def status_text(self):
        if self.closed:
            return _("Closed")
        last_msg = self.message_set.last()
        if last_msg and last_msg.user == self.user:
            return _("Waiting for staff")
        else:
            return _("Open")

    def get_contacts(self):
        contacts = TicketNotifyAddress.objects.filter(category=self.category)
        return [c.address for c in contacts]

    def notify_new(self, first_message):
        url = ROOT_URL + reverse('tickets:view', args=(self.id,))
        subject = _("Ticket:") + " " + self.subject
        ctx = dict(ticket=self, message=first_message, url=url)
        notify(subject, 'tickets/mail_support_new.txt', self.get_contacts(), ctx)

    def notify_reply(self, message):
        url = ROOT_URL + reverse('tickets:view', args=(self.id,))
        subject = _("Ticket:") + " " + self.subject
        ctx = dict(ticket=self, message=message, url=url)
        notify(subject, 'tickets/mail_support_reply.txt', self.get_contacts(), ctx)
        if self.user and self.user.email:
            if message.staff_only and not self.user.has_perm('tickets.view_private_message'):
                return
            notify(subject, 'tickets/mail_user_reply.txt', [self.user.email], ctx)

    def notify_close(self):
        url = ROOT_URL + reverse('tickets:view', args=(self.id,))
        subject = _("Ticket:") + " " + self.subject
        ctx = dict(ticket=self, url=url)
        notify(subject, 'tickets/mail_user_close.txt', [self.user.email], ctx)

    def __str__(self):
        return self.subject

    def get_absolute_url(self):
        return reverse('tickets:view', args=(self.id,))


class TicketNotifyAddress(models.Model):
    category = models.CharField(max_length=16, choices=CATEGORY_CHOICES)
    address = models.EmailField()


class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='message_set',
                               on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                             on_delete=models.SET_NULL)
    remote_addr = models.GenericIPAddressField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    staff_only = models.BooleanField(default=False)

    class Meta:
        ordering = ('created',)
