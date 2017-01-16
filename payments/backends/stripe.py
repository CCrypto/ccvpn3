import json

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from .base import BackendBase


class StripeBackend(BackendBase):
    backend_id = 'stripe'
    backend_verbose_name = _("Stripe")
    backend_display_name = _("Credit Card")
    backend_has_recurring = True

    def get_plan_id(self, period):
        return 'ccvpn_' + period

    def __init__(self, settings):
        if 'API_KEY' not in settings or 'PUBLIC_KEY' not in settings:
            return

        import stripe
        self.stripe = stripe

        stripe.api_key = settings['API_KEY']
        self.pubkey = settings['PUBLIC_KEY']
        self.header_image = settings.get('HEADER_IMAGE', '')
        self.currency = settings.get('CURRENCY', 'EUR')
        self.name = settings.get('NAME', 'VPN Payment')

        self.backend_enabled = True

    def new_payment(self, payment):
        desc = str(payment.time) + ' for ' + payment.user.username
        form = '''
        <form action="{post}" method="POST">
          <script
            src="https://checkout.stripe.com/checkout.js" class="stripe-button"
            data-key="{pubkey}"
            data-image="{img}"
            data-name="{name}"
            data-currency="{curr}"
            data-description="{desc}"
            data-amount="{amount}"
            data-email="{email}"
            data-locale="auto"
            data-zip-code="true"
            data-alipay="true">
          </script>
        </form>
        '''
        return form.format(
            post=reverse('payments:cb_stripe', args=(payment.id,)),
            pubkey=self.pubkey,
            img=self.header_image,
            email=payment.user.email or '',
            name=self.name,
            desc=desc,
            amount=payment.amount,
            curr=self.currency,
        )

    def new_subscription(self, subscr):
        desc = 'Subscription (' + str(subscr.period) + ') for ' + subscr.user.username
        form = '''
        <form action="{post}" method="POST">
          <script
            src="https://checkout.stripe.com/checkout.js" class="stripe-button"
            data-key="{pubkey}"
            data-image="{img}"
            data-name="{name}"
            data-currency="{curr}"
            data-description="{desc}"
            data-amount="{amount}"
            data-email="{email}"
            data-locale="auto"
            data-zip-code="true"
            data-alipay="true">
          </script>
        </form>
        '''
        return form.format(
            post=reverse('payments:cb_stripe_subscr', args=(subscr.id,)),
            pubkey=self.pubkey,
            img=self.header_image,
            email=subscr.user.email or '',
            name=self.name,
            desc=desc,
            amount=subscr.period_amount,
            curr=self.currency,
        )

    def cancel_subscription(self, subscr):
        if subscr.status not in ('new', 'unconfirmed', 'active'):
            return

        try:
            cust = self.stripe.Customer.retrieve(subscr.backend_extid)
        except self.stripe.error.InvalidRequestError:
            return

        try:
            # Delete customer and cancel any active subscription
            cust.delete()
        except self.stripe.error.InvalidRequestError:
            pass

        subscr.status = 'cancelled'
        subscr.save()

    def callback(self, payment, request):
        post_data = request.POST

        token = post_data.get('stripeToken')
        if not token:
            payment.status = 'cancelled'
            payment.status_message = _("No payment information was received.")
            return

        months = int(payment.time.days / 30)
        username = payment.user.username

        try:
            charge = self.stripe.Charge.create(
                amount=payment.amount,
                currency=self.currency,
                card=token,
                description="%d months for %s" % (months, username),
            )
            payment.backend_extid = charge['id']

            if charge['refunded'] or not charge['paid']:
                payment.status = 'rejected'
                payment.status_message = _("The payment has been refunded or rejected.")
                payment.save()
                return

            payment.paid_amount = int(charge['amount'])

            if payment.paid_amount < payment.amount:
                payment.status = 'error'
                payment.status_message = _("The paid amount is under the required amount.")
                payment.save()
                return

            payment.status = 'confirmed'
            payment.status_message = None
            payment.save()
            payment.user.vpnuser.add_paid_time(payment.time)
            payment.user.vpnuser.on_payment_confirmed(payment)
            payment.user.vpnuser.save()

        except self.stripe.error.CardError as e:
            payment.status = 'rejected'
            payment.status_message = e.json_body['error']['message']
            payment.save()

    def callback_subscr(self, subscr, request):
        post_data = request.POST
        token = post_data.get('stripeToken')
        if not token:
            subscr.status = 'cancelled'
            subscr.save()
            return

        try:
            cust = self.stripe.Customer.create(
                source=token,
                plan=self.get_plan_id(subscr.period),
            )
        except self.stripe.error.InvalidRequestError:
            return
        except self.stripe.CardError as e:
            subscr.status = 'error'
            subscr.backend_data['stripe_error'] = e.json_body['error']['message']
            return

        try:
            if subscr.status == 'new':
                subscr.status = 'unconfirmed'
            subscr.backend_extid = cust['id']
            subscr.save()
        except (self.stripe.error.InvalidRequestError, self.stripe.error.CardError) as e:
            subscr.status = 'error'
            subscr.backend_data['stripe_error'] = e.json_body['error']['message']
            subscr.save()

    def webhook_payment_succeeded(self, event):
        from payments.models import Subscription, Payment

        invoice = event['data']['object']
        customer_id = invoice['customer']

        # Prevent making duplicate Payments if event is received twice
        pc = Payment.objects.filter(backend_extid=invoice['id']).count()
        if pc > 0:
            return

        subscr = Subscription.objects.get(backend_extid=customer_id)
        payment = subscr.create_payment()
        payment.status = 'confirmed'
        payment.paid_amount = invoice['total']
        payment.backend_extid = invoice['id']
        payment.backend_data = {'event_id': event['id']}
        payment.save()

        payment.user.vpnuser.add_paid_time(payment.time)
        payment.user.vpnuser.on_payment_confirmed(payment)
        payment.user.vpnuser.save()
        payment.save()

        subscr.status = 'active'
        subscr.save()

    def webhook(self, request):
        try:
            event_json = json.loads(request.body.decode('utf-8'))
            event = self.stripe.Event.retrieve(event_json["id"])
        except (ValueError, self.stripe.error.InvalidRequestError):
            return False

        if event['type'] == 'invoice.payment_succeeded':
            self.webhook_payment_succeeded(event)
        return True

    def get_ext_url(self, payment):
        if not payment.backend_extid:
            return None
        return 'https://dashboard.stripe.com/payments/%s' % payment.backend_extid

    def get_subscr_ext_url(self, subscr):
        if not subscr.backend_extid:
            return None
        return 'https://dashboard.stripe.com/customers/%s' % subscr.backend_extid
