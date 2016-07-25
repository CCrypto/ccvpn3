import random
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from . import core

assert isinstance(settings.TRIAL_PERIOD, timedelta)
assert isinstance(settings.TRIAL_PERIOD_LIMIT, int)

prng = random.SystemRandom()


def random_gift_code():
    charset = "123456789ABCDEFGHIJKLMNPQRSTUVWXYZ"
    return ''.join([prng.choice(charset) for n in range(10)])


class VPNUser(models.Model):
    class Meta:
        verbose_name = _("VPN User")
        verbose_name_plural = _("VPN Users")

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)

    expiration = models.DateTimeField(blank=True, null=True)
    last_expiry_notice = models.DateTimeField(blank=True, null=True)
    notify_expiration = models.BooleanField(default=True)

    trial_periods_given = models.IntegerField(default=0)

    last_vpn_auth = models.DateTimeField(blank=True, null=True)

    referrer = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL,
                                 related_name='referrals')
    referrer_used = models.BooleanField(default=False)

    @property
    def is_paid(self):
        if not self.expiration:
            return False
        return self.expiration > timezone.now()

    @property
    def time_left(self):
        return timezone.now() - self.expiration

    def add_paid_time(self, time):
        now = timezone.now()
        if not self.expiration or self.expiration < now:
            self.expiration = now
        self.expiration += time

        # Propagate update to core
        if core.VPN_AUTH_STORAGE == 'core':
            core.update_user_expiration(self.user)

    def give_trial_period(self):
        self.add_paid_time(settings.TRIAL_PERIOD)
        self.trial_periods_given += 1

    @property
    def can_have_trial(self):
        if self.trial_periods_given >= settings.TRIAL_PERIOD_LIMIT:
            return False
        if self.user.payment_set.filter(status='confirmed').count() > 0:
            return False
        return True

    @property
    def remaining_trial_periods(self):
        return settings.TRIAL_PERIOD_LIMIT - self.trial_periods_given

    def on_payment_confirmed(self, payment):
        if self.referrer and not self.referrer_used:
            self.referrer.vpnuser.add_paid_time(timedelta(days=14))
            self.referrer.vpnuser.save()
            self.referrer_used = True

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_vpnuser(sender, instance, created, **kwargs):
    if created:
        VPNUser.objects.create(user=instance)


class GiftCode(models.Model):
    class Meta:
        verbose_name = _("Gift Code")
        verbose_name_plural = _("Gift Codes")

    code = models.CharField(max_length=32, default=random_gift_code)
    time = models.DurationField(default=timedelta(days=30))
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='created_giftcode_set',
                                   on_delete=models.CASCADE, null=True, blank=True)
    single_use = models.BooleanField(default=True)
    free_only = models.BooleanField(default=True)
    available = models.BooleanField(default=True)
    comment = models.TextField(blank=True)
    users = models.ManyToManyField(User, through='GiftCodeUser')

    def use_on(self, user):
        if not self.available:
            return False
        if self.free_only and user.vpnuser.is_paid:
            return False

        link = GiftCodeUser(user=user, code=self)
        link.save()

        user.vpnuser.add_paid_time(self.time)
        user.vpnuser.save()

        if self.single_use:
            self.available = False

        self.save()

        return True

    @property
    def comment_head(self):
        head = self.comment.split('\n', 1)[0]
        if len(head) > 80:
            head = head[:80] + "..."
        return head

    def __str__(self):
        return self.code


class GiftCodeUser(models.Model):
    class Meta:
        verbose_name = _("Gift Code User")
        verbose_name_plural = _("Gift Code Users")

    user = models.ForeignKey(User)
    code = models.ForeignKey(GiftCode)
    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return "%s (%s)" % (self.user.username, self.code.code)

