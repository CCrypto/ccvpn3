from datetime import timedelta
from io import StringIO

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.db.models import Count
from django.utils import timezone


def get_prev_month(d):
    if d.month == 1:
        year = d.year - 1
        month = 12
    else:
        year = d.year
        month = d.month - 1
    return d.replace(month=month, year=year)


def should_bill(report, user, time_limit):
    """ Determines if one user has actually paid for the current month """

    # Here for consistency, should be filtered in the query
    if not user.vpnuser.expiration or user.vpnuser.expiration < time_limit:
        return False

    # Replay payments
    payments = list(user.payment_set.order_by('id').filter(status='confirmed'))
    paid_expiration = None
    for p in payments:
        d = p.confirmed_on or p.created
        paid_expiration = max(paid_expiration or d, d) + p.time

    # Numbre of days paid after the start of the month
    # If negative and not filtered with vpnuser.expiration, user was given time.
    # If positive, user has paid for this time.
    delta = paid_expiration - time_limit

    if delta < timedelta():
        report.write("- %s (#%d): %s\n" % (user.username, user.id, -delta))

    return delta > timedelta()


class Command(BaseCommand):
    help = "Generate and send a monthly usage report to ADMINS"

    def handle(self, *args, **options):
        addresses = settings.USAGE_REPORT_DESTINATION

        def format_e(n):
            return '%.2f%s' % (n / 100, settings.PAYMENTS_CURRENCY[1])

        # Dates
        end = timezone.now().replace(microsecond=0, second=0, minute=0, hour=0, day=5)
        start = get_prev_month(end)

        # Filter users
        filtering_report = StringIO()
        all_users = User.objects.order_by('id')
        active_users = all_users.filter(vpnuser__expiration__gt=start)
        paying_users = active_users.filter(payment__status='confirmed').annotate(Count('payment')).filter(payment__count__gt=0)
        users = [u for u in paying_users if should_bill(filtering_report, u, start)]

        # Generate report
        report = "CCVPN Usage Report\n"
        report += "==================\n\n"

        report += "From: %s\nTo  : %s\n\n" % (start, end)

        keys = ('Users', 'Active', 'W/Payment', 'Selected')
        values = (all_users.count(), active_users.count(), paying_users.count(), len(users))
        report += " | ".join("%-10s" % s for s in keys) + "\n"
        report += " | ".join("%-10s" % s for s in values) + "\n"
        report += "\n"

        user_cost = settings.VPN_USER_COST
        total_cost = settings.VPN_USER_COST * len(users)

        report += "Billed: %d * %s = %s\n" % (len(users), format_e(user_cost), format_e(total_cost))
        report += "\n"

        if filtering_report.getvalue():
            report += "Ignored users:\n"
            report += filtering_report.getvalue()
            report += "\n"

        users_text = "\n".join("%s (#%d)" % (u.username, u.id) for u in users)

        subject = "[CCVPN] Usage Report: %s to %s" % (
            start.strftime('%m/%Y'), end.strftime('%m/%Y'))

        # Send
        print(report)
        print("-------")
        print("Send to: " + ", ".join(a for a in addresses))

        print("Confirm? [y/n] ", end='')
        i = input()
        if i.lower().strip() != 'y':
            return

        for dest in addresses:
            mail = EmailMessage(subject=subject, body=report,
                                from_email=settings.DEFAULT_FROM_EMAIL, to=[dest])
            mail.attach('users.txt', users_text, 'text/plain')
            mail.send()

        print("Sent.")


