from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from datetime import timedelta

from ccvpn.common import get_price
from .backends import BackendBase

backends_settings = settings.PAYMENTS_BACKENDS
assert isinstance(backends_settings, dict)

CURRENCY_CODE, CURRENCY_NAME = settings.PAYMENTS_CURRENCY

STATUS_CHOICES = (
    ('new', _("Waiting for payment")),
    ('confirmed', _("Confirmed")),
    ('cancelled', _("Cancelled")),
    ('rejected', _("Rejected by processor")),
    ('error', _("Payment processing failed")),
)

# A Subscription is created with status='new'. When getting back from PayPal,
# it may get upgraded to 'unconfirmed'. It will be set 'active' with the first
# confirmed payment.
# 'unconfirmed' exists to prevent creation of a second Subscription while
# waiting for the first one to be confirmed.
SUBSCR_STATUS_CHOICES = (
    ('new', _("Created")),
    ('unconfirmed', _("Waiting for payment")),
    ('active', _("Active")),
    ('cancelled', _("Cancelled")),
    ('error', _("Error")),
)

SUBSCR_PERIOD_CHOICES = (
    ('3m', _("Every 3 months")),
    ('6m', _("Every 6 months")),
    ('12m', _("Every year")),
)

# All known backends (classes)
BACKENDS = {}
BACKEND_CHOICES = []

# All enabled backends (configured instances)
ACTIVE_BACKENDS = {}
ACTIVE_BACKEND_CHOICES = []

for cls in BackendBase.__subclasses__():
    name = cls.backend_id
    assert isinstance(name, str)

    if name not in backends_settings:
        continue

    backend_settings = backends_settings.get(name, {})
    for k, v in backend_settings.items():
        if hasattr(v, '__call__'):
            backend_settings[k] = v()

    obj = cls(backend_settings)
    if not obj.backend_enabled:
        if name in backends_settings:
            raise Exception("Invalid settings for payment backend %r" % name)

    BACKENDS[name] = obj
    BACKEND_CHOICES.append((name, cls.backend_verbose_name))

    if obj.backend_enabled:
        ACTIVE_BACKENDS[name] = obj
        ACTIVE_BACKEND_CHOICES.append((name, cls.backend_verbose_name))

BACKEND_CHOICES = sorted(BACKEND_CHOICES, key=lambda x: x[0])
ACTIVE_BACKEND_CHOICES = sorted(ACTIVE_BACKEND_CHOICES, key=lambda x: x[0])


def period_months(p):
    return {
        '3m': 3,
        '6m': 6,
        '12m': 12,
    }[p]


class Payment(models.Model):
    """ Just a payment.
    If subscription is not null, it has been automatically issued.
    backend_extid is the external transaction ID, backend_data is other
    things that should only be used by the associated backend.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    backend_id = models.CharField(max_length=16, choices=BACKEND_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='new')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    confirmed_on = models.DateTimeField(null=True, blank=True)
    amount = models.IntegerField()
    paid_amount = models.IntegerField(default=0)
    time = models.DurationField()
    subscription = models.ForeignKey('Subscription', null=True, blank=True)
    status_message = models.TextField(blank=True, null=True)

    backend_extid = models.CharField(max_length=64, null=True, blank=True)
    backend_data = JSONField(blank=True)

    @property
    def currency_code(self):
        return CURRENCY_CODE

    @property
    def currency_name(self):
        return CURRENCY_NAME

    @property
    def backend(self):
        """ Returns a global instance of the backend
        :rtype: BackendBase
        """
        return BACKENDS[self.backend_id]

    def get_amount_display(self):
        return '%.2f %s' % (self.amount / 100, CURRENCY_NAME)

    @property
    def is_confirmed(self):
        return self.status == 'confirmed'

    class Meta:
        ordering = ('-created', )

    @classmethod
    def create_payment(self, backend_id, user, months):
        payment = Payment(
            user=user,
            backend_id=backend_id,
            status='new',
            time=timedelta(days=30 * months),
            amount=get_price() * months
        )
        return payment


class Subscription(models.Model):
    """ Recurring payment subscription. """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    backend_id = models.CharField(max_length=16, choices=BACKEND_CHOICES)
    created = models.DateTimeField(auto_now_add=True)
    period = models.CharField(max_length=16, choices=SUBSCR_PERIOD_CHOICES)
    last_confirmed_payment = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=16, choices=SUBSCR_STATUS_CHOICES, default='new')

    backend_extid = models.CharField(max_length=64, null=True, blank=True)
    backend_data = JSONField(blank=True)

    @property
    def backend(self):
        """ Returns a global instance of the backend
        :rtype: BackendBase
        """
        return BACKENDS[self.backend_id]

    @property
    def months(self):
        return period_months(self.period)

    @property
    def period_amount(self):
        return self.months * get_price()

    @property
    def next_renew(self):
        """ Approximate date of the next payment """
        if self.last_confirmed_payment:
            return self.last_confirmed_payment + timedelta(days=self.months * 30)
        return self.created + timedelta(days=self.months * 30)

    @property
    def monthly_amount(self):
        return get_price()

    def create_payment(self):
        payment = Payment(
            user=self.user,
            backend_id=self.backend_id,
            status='new',
            time=timedelta(days=30 * self.months),
            amount=get_price() * self.months,
            subscription=self,
        )
        return payment


