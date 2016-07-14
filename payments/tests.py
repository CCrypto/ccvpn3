from datetime import timedelta
from urllib.parse import parse_qs

from django.test import TestCase, RequestFactory
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User

from .models import Payment
from .backends import BitcoinBackend, PaypalBackend, StripeBackend

from decimal import Decimal


class FakeBTCRPCNew:
    def getnewaddress(self, account):
        return 'TEST_ADDRESS'


class FakeBTCRPCUnpaid:
    def getreceivedbyaddress(self, address):
        assert address == 'TEST_ADDRESS'
        return Decimal('0')


class FakeBTCRPCPartial:
    def getreceivedbyaddress(self, address):
        assert address == 'TEST_ADDRESS'
        return Decimal('0.5') * 100000000


class FakeBTCRPCPaid:
    def getreceivedbyaddress(self, address):
        assert address == 'TEST_ADDRESS'
        return Decimal('1') * 100000000


PAYPAL_IPN_TEST = '''\
mc_gross=3.00&\
protection_eligibility=Eligible&\
address_status=confirmed&\
payer_id=LPLWNMTBWMFAY&\
tax=0.00&\
address_street=1+Main+St&\
payment_date=20%3A12%3A59+Jan+13%2C+2009+PST&\
payment_status=Completed&\
charset=windows-1252&\
address_zip=95131&\
first_name=Test&\
mc_fee=0.88&\
address_country_code=US&\
address_name=Test+User&\
notify_version=2.6&\
custom=&\
payer_status=verified&\
address_country=United+States&\
address_city=San+Jose&\
quantity=1&\
verify_sign=AtkOfCXbDm2hu0ZELryHFjY-Vb7PAUvS6nMXgysbElEn9v-1XcmSoGtf&\
payer_email=test_user@example.com&\
txn_id=61E67681CH3238416&\
payment_type=instant&\
last_name=User&\
address_state=CA&\
receiver_email=test_business@example.com&\
payment_fee=0.88&\
receiver_id=S8XGHLYDW9T3S&\
txn_type=express_checkout&\
item_name=&\
mc_currency=EUR&\
item_number=&\
residence_country=US&\
test_ipn=1&\
handling_amount=0.00&\
transaction_subject=&\
payment_gross=3.00&\
shipping=0.00'''


class BitcoinBackendTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test_user@example.com', None)

        self.p = Payment.objects.create(
            user=self.user, time=timedelta(days=30), backend='bitcoin',
            amount=300)

    def test_new(self):
        backend = BitcoinBackend(dict(BITCOIN_VALUE=300, URL=''))
        backend.make_rpc = FakeBTCRPCNew

        backend.new_payment(self.p)
        redirect = backend.new_payment(self.p)
        self.assertEqual(self.p.backend_extid, 'TEST_ADDRESS')
        self.assertEqual(self.p.status, 'new')
        self.assertIn('btc_price', self.p.backend_data)
        self.assertIn('btc_address', self.p.backend_data)
        self.assertEqual(self.p.backend_data['btc_address'], 'TEST_ADDRESS')
        self.assertIsInstance(redirect, HttpResponseRedirect)
        self.assertEqual(redirect.url, '/payments/view/%d' % self.p.id)
        self.assertEqual(self.p.status_message, "Please send 1.00000 BTC to TEST_ADDRESS")

    def test_rounding(self):
        """ Rounding test
        300 / 300 = 1 => 1.00000 BTC
        300 / 260 = Decimal('1.153846153846153846153846154') => 1.15385 BTC
        """
        backend = BitcoinBackend(dict(BITCOIN_VALUE=300, URL=''))
        backend.make_rpc = FakeBTCRPCNew
        backend.new_payment(self.p)
        self.assertEqual(self.p.status_message, "Please send 1.00000 BTC to TEST_ADDRESS")

        backend = BitcoinBackend(dict(BITCOIN_VALUE=260, URL=''))
        backend.make_rpc = FakeBTCRPCNew
        backend.new_payment(self.p)
        self.assertEqual(self.p.status_message, "Please send 1.15385 BTC to TEST_ADDRESS")


class BitcoinBackendConfirmTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test_user@example.com', None)

        self.p = Payment.objects.create(
            user=self.user, time=timedelta(days=30), backend='bitcoin',
            amount=300)

        # call new_payment
        backend = BitcoinBackend(dict(BITCOIN_VALUE=300, URL=''))
        backend.make_rpc = FakeBTCRPCNew
        backend.new_payment(self.p)

    def test_check_unpaid(self):
        backend = BitcoinBackend(dict(BITCOIN_VALUE=300, URL=''))
        backend.make_rpc = FakeBTCRPCUnpaid

        backend.check(self.p)
        self.assertEqual(self.p.status, 'new')
        self.assertEqual(self.p.paid_amount, 0)

    def test_check_partially_paid(self):
        backend = BitcoinBackend(dict(BITCOIN_VALUE=300, URL=''))
        backend.make_rpc = FakeBTCRPCPartial
        backend.check(self.p)
        self.assertEqual(self.p.status, 'new')
        self.assertEqual(self.p.paid_amount, 150)

    def test_check_paid(self):
        backend = BitcoinBackend(dict(BITCOIN_VALUE=300, URL=''))
        backend.make_rpc = FakeBTCRPCPaid
        backend.check(self.p)
        self.assertEqual(self.p.paid_amount, 300)
        self.assertEqual(self.p.status, 'confirmed')


class BackendTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test_user@example.com', None)

    def test_paypal(self):
        # TODO: This checks the most simple and perfect payment that could
        # happen, but not errors or other/invalid IPN

        payment = Payment.objects.create(
            user=self.user,
            time=timedelta(days=30),
            backend='paypal',
            amount=300
        )

        settings = dict(
            TEST=True,
            TITLE='Test Title',
            CURRENCY='EUR',
            ADDRESS='test_business@example.com',
        )

        with self.settings(ROOT_URL='root'):
            backend = PaypalBackend(settings)
            redirect = backend.new_payment(payment)

        self.assertIsInstance(redirect, HttpResponseRedirect)

        host, params = redirect.url.split('?', 1)
        params = parse_qs(params)

        expected_notify_url = 'root/payments/callback/paypal/%d' % payment.id
        expected_return_url = 'root/payments/view/%d' % payment.id
        expected_cancel_url = 'root/payments/cancel/%d' % payment.id

        self.assertEqual(params['cmd'][0], '_xclick')
        self.assertEqual(params['notify_url'][0], expected_notify_url)
        self.assertEqual(params['return'][0], expected_return_url)
        self.assertEqual(params['cancel_return'][0], expected_cancel_url)
        self.assertEqual(params['business'][0], 'test_business@example.com')
        self.assertEqual(params['currency_code'][0], 'EUR')
        self.assertEqual(params['amount'][0], '3.00')
        self.assertEqual(params['item_name'][0], 'Test Title')

        # Replace PaypalBackend.verify_ipn to not call the PayPal API
        # we will assume the IPN is authentic
        backend.verify_ipn = lambda payment, request: True

        ipn_url = '/payments/callback/paypal/%d' % payment.id
        ipn_request = RequestFactory().post(
            ipn_url,
            content_type='application/x-www-form-urlencoded',
            data=PAYPAL_IPN_TEST)
        r = backend.callback(payment, ipn_request)

        self.assertTrue(r)
        self.assertEqual(payment.status, 'confirmed')
        self.assertEqual(payment.paid_amount, 300)
        self.assertEqual(payment.backend_extid, '61E67681CH3238416')

    def test_paypal_ipn_error(self):
        payment = Payment.objects.create(
            user=self.user,
            time=timedelta(days=30),
            backend='paypal',
            amount=300
        )

        settings = dict(
            TEST=True,
            TITLE='Test Title',
            CURRENCY='EUR',
            ADDRESS='test_business@example.com',
        )

        with self.settings(ROOT_URL='root'):
            backend = PaypalBackend(settings)
            redirect = backend.new_payment(payment)

        self.assertIsInstance(redirect, HttpResponseRedirect)

        host, params = redirect.url.split('?', 1)
        params = parse_qs(params)

        expected_notify_url = 'root/payments/callback/paypal/%d' % payment.id

        # Replace PaypalBackend.verify_ipn to not call the PayPal API
        # we will assume the IPN is authentic
        backend.verify_ipn = lambda payment, request: True

        ipn_url = '/payments/callback/paypal/%d' % payment.id
        ipn_request = RequestFactory().post(
            ipn_url,
            content_type='application/x-www-form-urlencoded',
            data=PAYPAL_IPN_TEST)
        r = backend.callback(payment, ipn_request)

        self.assertTrue(r)
        self.assertEqual(payment.status, 'confirmed')
        self.assertEqual(payment.paid_amount, 300)
        self.assertEqual(payment.backend_extid, '61E67681CH3238416')

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

