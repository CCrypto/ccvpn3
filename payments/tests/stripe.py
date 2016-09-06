from datetime import timedelta

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

from payments.models import Payment
from payments.backends import StripeBackend


class StripeBackendTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test_user@example.com', None)

    def test_stripe(self):
        payment = Payment.objects.create(
            user=self.user,
            time=timedelta(days=30),
            backend='stripe',
            amount=300
        )

        settings = dict(
            API_KEY='test_secret_key',
            PUBLIC_KEY='test_public_key',
            CURRENCY='EUR',
            NAME='Test Name',
        )

        with self.settings(ROOT_URL='root'):
            backend = StripeBackend(settings)
            form_html = backend.new_payment(payment)

        expected_form = '''
        <form action="/payments/callback/stripe/{id}" method="POST">
          <script
            src="https://checkout.stripe.com/checkout.js" class="stripe-button"
            data-key="test_public_key"
            data-image=""
            data-name="Test Name"
            data-currency="EUR"
            data-description="30 days, 0:00:00 for test"
            data-amount="300"
            data-email="test_user@example.com"
            data-locale="auto"
            data-zip-code="true"
            data-alipay="true">
          </script>
        </form>
        '''.format(id=payment.id)
        self.maxDiff = None
        self.assertEqual(expected_form, form_html)

        def create_charge(**kwargs):
            self.assertEqual(kwargs, {
                'amount': 300,
                'currency': 'EUR',
                'card': 'TEST_TOKEN',
                'description': "1 months for test",
            })
            return {
                'id': 'TEST_CHARGE_ID',
                'refunded': False,
                'paid': True,
                'amount': 300,
            }

        # Replace the Stripe api instance
        backend.stripe = type('Stripe', (object, ), {
            'Charge': type('Charge', (object, ), {
                'create': create_charge,
            }),
            'error': type('error', (object, ), {
                'CardError': type('CardError', (Exception, ), {}),
            }),
        })

        request = RequestFactory().post('', {'stripeToken': 'TEST_TOKEN'})
        backend.callback(payment, request)

        self.assertEqual(payment.backend_extid, 'TEST_CHARGE_ID')

