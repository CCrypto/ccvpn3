from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from payments.models import ACTIVE_BACKENDS, SUBSCR_PERIOD_CHOICES, period_months

CURRENCY_CODE, CURRENCY_NAME = settings.PAYMENTS_CURRENCY
MONTHLY_PRICE = settings.PAYMENTS_MONTHLY_PRICE


class Command(BaseCommand):
    help = "Update Stripe plans"

    def add_arguments(self, parser):
        parser.add_argument('--force-run', action='store_true',
                            help="Run even when Stripe backend is disabled")
        parser.add_argument('--force-update', action='store_true',
                            help="Replace plans, including matching ones")

    def handle(self, *args, **options):
        if 'stripe' not in ACTIVE_BACKENDS and options['force-run'] is False:
            raise CommandError("stripe backend not active.")

        backend = ACTIVE_BACKENDS['stripe']
        stripe = backend.stripe

        for period_id, period_name in SUBSCR_PERIOD_CHOICES:
            plan_id = backend.get_plan_id(period_id)
            months = period_months(period_id)
            amount = months * MONTHLY_PRICE

            kwargs = dict(
                id=plan_id,
                amount=months * MONTHLY_PRICE,
                interval='month',
                interval_count=months,
                name=backend.name + " (%s)" % period_id,
                currency=CURRENCY_CODE,
            )

            self.stdout.write('Plan %s: %d months for %.2f %s (%s)... ' % (
                plan_id, months, amount / 100, CURRENCY_NAME, CURRENCY_CODE), ending='')
            self.stdout.flush()

            try:
                plan = stripe.Plan.retrieve(plan_id)
            except stripe.error.InvalidRequestError:
                plan = None

            def is_valid_plan():
                if not plan:
                    return False
                for k, v in kwargs.items():
                    if getattr(plan, k) != v:
                        return False
                return True

            if plan:
                if is_valid_plan() and not options['force_update']:
                    self.stdout.write(self.style.SUCCESS('[ok]'))
                    continue
                plan.delete()
                update = True
            else:
                update = False

            stripe.Plan.create(**kwargs)
            if update:
                self.stdout.write(self.style.WARNING('[updated]'))
            else:
                self.stdout.write(self.style.WARNING('[created]'))
