from django.core.management.base import BaseCommand, CommandError

from payments.models import Payment, ACTIVE_BACKENDS


class Command(BaseCommand):
    help = "Check bitcoin payments status"

    def handle(self, *args, **options):
        if 'bitcoin' not in ACTIVE_BACKENDS:
            raise CommandError("bitcoin backend not active.")

        backend = ACTIVE_BACKENDS['bitcoin']

        payments = Payment.objects.filter(backend_id='bitcoin', status='new')

        self.stdout.write("Found %d active unconfirmed payments." % len(payments))

        for p in payments:
            self.stdout.write("Checking payment #%d... " % p.id, ending="")
            backend.check(p)

            if p.status == 'confirmed':
                self.stdout.write("OK.")
            else:
                self.stdout.write("Waiting")


