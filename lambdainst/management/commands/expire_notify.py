from django.core.management.base import BaseCommand

from datetime import timedelta

from django.db.models import Q, F
from django.conf import settings
from django.utils import timezone
from django.template.loader import get_template
from django.core.mail import send_mass_mail
from constance import config as site_config

from ccvpn.common import parse_integer_list
from lambdainst.models import VPNUser

ROOT_URL = settings.ROOT_URL
SITE_NAME = settings.TICKETS_SITE_NAME


def get_next_expirations(days=3):
    """ Gets users whose subscription will expire in some days """

    limit_date = timezone.now() + timedelta(days=days)

    users = VPNUser.objects.exclude(user__email__exact='')

    users = users.filter(expiration__gt=timezone.now())  # Not expired
    users = users.filter(expiration__lt=limit_date)  # Expire in a few days

    # Make sure we dont send the notice twice
    users = users.filter(Q(last_expiry_notice__isnull=True)
                         | Q(expiration__gt=F('last_expiry_notice')
                             + timedelta(days=days)))
    return users


class Command(BaseCommand):
    help = "Notify users near the end of their subscription"

    def handle(self, *args, **options):
        from_email = settings.DEFAULT_FROM_EMAIL

        for v in parse_integer_list(site_config.NOTIFY_DAYS_BEFORE):
            emails = []
            qs = get_next_expirations(v)
            users = list(qs)
            for u in users:
                # Ignore users with active subscriptions
                # They will get notified only if it gets cancelled (payments
                # processors will cancel after a few failed payments)
                if u.get_subscription():
                    continue

                ctx = dict(site_name=SITE_NAME, user=u.user,
                           exp=u.expiration, url=ROOT_URL)
                text = get_template('lambdainst/mail_expire_soon.txt').render(ctx)
                emails.append(("CCVPN Expiration", text, from_email, [u.user.email]))
                self.stdout.write("sending -%d days notify to %s ..." % (v, u.user.email))

            send_mass_mail(emails)
            qs.update(last_expiry_notice=timezone.now())
