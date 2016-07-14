from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField

from .backends import BackendBase

backend_settings = settings.PAYMENTS_BACKENDS
assert isinstance(backend_settings, dict)

CURRENCY_CODE, CURRENCY_NAME = settings.PAYMENTS_CURRENCY

STATUS_CHOICES = (
    ('new', _("Waiting for payment")),
    ('confirmed', _("Confirmed")),
    ('cancelled', _("Cancelled")),
    ('rejected', _("Rejected by processor")),
    ('error', _("Payment processing failed")),
)

PERIOD_CHOICES = (
    ('6m', _("Every 6 months")),
    ('1year', _("Yearly")),
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

    obj = cls(backend_settings.get(name, {}))
    if not obj.backend_enabled:
        if name in backend_settings:
            raise Exception("Invalid settings for payment backend %r" % name)

    BACKENDS[name] = obj
    BACKEND_CHOICES.append((name, cls.backend_verbose_name))

    if obj.backend_enabled:
        ACTIVE_BACKENDS[name] = obj
        ACTIVE_BACKEND_CHOICES.append((name, cls.backend_verbose_name))

BACKEND_CHOICES = sorted(BACKEND_CHOICES, key=lambda x: x[0])
ACTIVE_BACKEND_CHOICES = sorted(ACTIVE_BACKEND_CHOICES, key=lambda x: x[0])


class Payment(models.Model):
    """ Just a payment.
    If recurring_source is not null, it has been automatically issued.
    backend_id is the external transaction ID, backend_data is other
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
    recurring_source = models.ForeignKey('RecurringPaymentSource', null=True, blank=True)
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


class RecurringPaymentSource(models.Model):
    """ Used as a source to periodically make Payments.
    They use the same backends.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    backend = models.CharField(max_length=16, choices=BACKEND_CHOICES)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    period = models.CharField(max_length=16, choices=PERIOD_CHOICES)
    last_confirmed_payment = models.DateTimeField(blank=True, null=True)

    backend_id = models.CharField(max_length=64, null=True, blank=True)
    backend_data = JSONField(blank=True)

