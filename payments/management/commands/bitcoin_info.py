from django.core.management.base import BaseCommand, CommandError

from payments.models import ACTIVE_BACKENDS


class Command(BaseCommand):
    help = "Get bitcoind info"

    def handle(self, *args, **options):
        if 'bitcoin' not in ACTIVE_BACKENDS:
            raise CommandError("bitcoin backend not active.")

        backend = ACTIVE_BACKENDS['bitcoin']
        for key, value in backend.get_info():
            self.stdout.write("%s: %s" % (key, value))
