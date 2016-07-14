from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_duration

from payments.models import Payment


class Command(BaseCommand):
    help = "Manually confirm a Payment"

    def add_arguments(self, parser):
        parser.add_argument('id', action='store', type=int, help="Payment ID")
        parser.add_argument('--paid-amount', dest='amount', action='store', type=int, help="Paid amount")
        parser.add_argument('--extid', dest='extid', action='store', type=str)
        parser.add_argument('-n', dest='sim', action='store_true', help="Simulate")

    def handle(self, *args, **options):
        try:
            p = Payment.objects.get(id=options['id'])
        except Payment.DoesNotExist:
            self.stderr.write("Cannot find payment #%d" % options['id'])
            return

        print("Payment #%d by %s (amount=%d; paid_amount=%d)" % (p.id, p.user.username, p.amount, p.paid_amount))

        if options['amount']:
            pa = options['amount']
        else:
            pa = p.amount

        extid = options['extid']

        print("Status -> confirmed")
        print("Paid amount -> %d" % pa)
        if extid:
            print("Ext ID -> %s" % extid)

        print("Confirm? [y/n] ")
        i = input()
        if i.lower().strip() == 'y':
            p.user.vpnuser.add_paid_time(p.time)
            p.user.vpnuser.on_payment_confirmed(p)
            p.user.vpnuser.save()

            p.paid_amount = pa
            p.status = 'confirmed'
            if extid:
                p.backend_extid = extid
            p.save()
        else:
            print("aborted.")

