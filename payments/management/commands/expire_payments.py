from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_duration

from payments.models import Payment


class Command(BaseCommand):
    help = "Cancels expired Payments"

    def add_arguments(self, parser):
        parser.add_argument('-n', dest='sim', action='store_true', help="Simulate")
        parser.add_argument('-e', '--exp-time', action='store',
                            help="Expiration time.", default='3 00:00:00')

    def handle(self, *args, **options):
        now = timezone.now()
        expdate = now - parse_duration(options['exp_time'])

        self.stdout.write("Now: " + now.isoformat())
        self.stdout.write("Exp: " + expdate.isoformat())

        expired = Payment.objects.filter(created__lte=expdate, status='new',
                                         paid_amount=0)

        for p in expired:
            self.stdout.write("Payment #%d (%s): %s" % (p.id, p.user.username, p.created))
            if not options['sim']:
                p.status = 'cancelled'
                p.save()

