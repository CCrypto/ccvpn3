from datetime import timedelta
from urllib.parse import parse_qs

from django.test import TestCase, RequestFactory
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User

from payments.models import Payment, Subscription
from payments.backends import PaypalBackend


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

PAYPAL_IPN_SUBSCR_PAYMENT = '''\
transaction_subject=VPN+Payment&\
payment_date=11%3A19%3A00+Sep+04%2C+2016+PDT&\
txn_type=subscr_payment&\
subscr_id=I-1S262863X133&\
last_name=buyer&\
residence_country=FR&\
item_name=VPN+Payment&\
payment_gross=&\
mc_currency=EUR&\
business=test_business@example.com&\
payment_type=instant&\
protection_eligibility=Ineligible&\
payer_status=verified&\
test_ipn=1&\
payer_email=test_user@example.com&\
txn_id=097872679P963871Y&\
receiver_email=test_business@example.com&\
first_name=test&\
payer_id=APYYVSFLNPWUU&\
receiver_id=MGT8TQ8GC4944&\
payment_status=Completed&\
payment_fee=&\
mc_fee=0.56&\
mc_gross=9.00&\
charset=windows-1252&\
notify_version=3.8&\
ipn_track_id=546a4aa4300a0'''


PAYPAL_IPN_SUBSCR_CANCEL = '''\
txn_type=subscr_cancel&\
subscr_id=I-E5SCT6936H40&\
last_name=buyer&\
residence_country=FR&\
mc_currency=EUR&\
item_name=VPN+Payment&\
business=test_business@example.com&\
recurring=1&\
payer_status=verified&\
test_ipn=1&\
payer_email=test_user@example.com&\
first_name=test&\
receiver_email=test_business@example.com&\
payer_id=APYYVSFLNPWUU&\
reattempt=1&\
subscr_date=17%3A35%3A14+Sep+04%2C+2016+PDT&\
charset=windows-1252&\
notify_version=3.8&\
period3=3+M&\
mc_amount3=9.00&\
ipn_track_id=474870d13b375'''


PAYPAL_IPN_SUBSCR_SIGNUP = '''\
txn_type=subscr_signup&\
subscr_id=I-1S262863X133&\
last_name=buyer&\
residence_country=FR&\
mc_currency=EUR&\
item_name=VPN+Payment&\
business=test_business@example.com&\
recurring=1&\
payer_status=verified&\
test_ipn=1&\
payer_email=test_user@example.com&\
first_name=test&\
receiver_email=test_business@example.com&\
payer_id=APYYVSFLNPWUU&\
reattempt=1&\
subscr_date=11%3A18%3A57+Sep+04%2C+2016+PDT&\
charset=windows-1252&\
notify_version=3.8&\
period3=3+M&\
mc_amount3=9.00&\
ipn_track_id=546a4aa4300a0'''


class PaypalBackendTest(TestCase):
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
        backend.verify_ipn = lambda request: True

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

        # Replace PaypalBackend.verify_ipn to not call the PayPal API
        # we will assume the IPN is authentic
        backend.verify_ipn = lambda request: True

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

    def test_paypal_subscr(self):
        subscription = Subscription.objects.create(
            user=self.user,
            backend='paypal',
            period='3m'
        )

        settings = dict(
            TEST=True,
            TITLE='Test Title',
            CURRENCY='EUR',
            ADDRESS='test_business@example.com',
        )

        with self.settings(ROOT_URL='root'):
            backend = PaypalBackend(settings)
            redirect = backend.new_subscription(subscription)

        self.assertIsInstance(redirect, HttpResponseRedirect)

        host, params = redirect.url.split('?', 1)
        params = parse_qs(params)

        expected_notify_url = 'root/payments/callback/paypal_subscr/%d' % subscription.id
        expected_return_url = 'root/payments/return_subscr/%d' % subscription.id
        expected_cancel_url = 'root/account/'

        self.assertEqual(params['cmd'][0], '_xclick-subscriptions')
        self.assertEqual(params['notify_url'][0], expected_notify_url)
        self.assertEqual(params['return'][0], expected_return_url)
        self.assertEqual(params['cancel_return'][0], expected_cancel_url)
        self.assertEqual(params['business'][0], 'test_business@example.com')
        self.assertEqual(params['currency_code'][0], 'EUR')
        self.assertEqual(params['a3'][0], '9.00')
        self.assertEqual(params['p3'][0], '3')
        self.assertEqual(params['t3'][0], 'M')
        self.assertEqual(params['item_name'][0], 'Test Title')

        # Replace PaypalBackend.verify_ipn to not call the PayPal API
        # we will assume the IPN is authentic
        backend.verify_ipn = lambda request: True

        self.assertEqual(subscription.status, 'new')

        # 1. the subscr_payment IPN
        ipn_url = '/payments/callback/paypal_subscr/%d' % subscription.id
        ipn_request = RequestFactory().post(
            ipn_url,
            content_type='application/x-www-form-urlencoded',
            data=PAYPAL_IPN_SUBSCR_PAYMENT)
        r = backend.callback_subscr(subscription, ipn_request)

        self.assertTrue(r)
        self.assertEqual(subscription.status, 'active')
        self.assertEqual(subscription.backend_extid, 'I-1S262863X133')

        payments = Payment.objects.filter(subscription=subscription).all()
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0].amount, 900)
        self.assertEqual(payments[0].paid_amount, 900)
        self.assertEqual(payments[0].backend_extid, '097872679P963871Y')

        # 2. the subscr_signup IPN
        # We don't expect anything to happen here
        ipn_url = '/payments/callback/paypal_subscr/%d' % subscription.id
        ipn_request = RequestFactory().post(
            ipn_url,
            content_type='application/x-www-form-urlencoded',
            data=PAYPAL_IPN_SUBSCR_SIGNUP)
        r = backend.callback_subscr(subscription, ipn_request)

        self.assertTrue(r)
        self.assertEqual(subscription.status, 'active')
        self.assertEqual(subscription.backend_extid, 'I-1S262863X133')

        payments = Payment.objects.filter(subscription=subscription).all()
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0].amount, 900)
        self.assertEqual(payments[0].paid_amount, 900)
        self.assertEqual(payments[0].backend_extid, '097872679P963871Y')

        # 3. the subscr_cancel IPN
        ipn_url = '/payments/callback/paypal_subscr/%d' % subscription.id
        ipn_request = RequestFactory().post(
            ipn_url,
            content_type='application/x-www-form-urlencoded',
            data=PAYPAL_IPN_SUBSCR_CANCEL)
        r = backend.callback_subscr(subscription, ipn_request)

        self.assertTrue(r)
        self.assertEqual(subscription.status, 'cancelled')
        self.assertEqual(subscription.backend_extid, 'I-1S262863X133')

        payments = Payment.objects.filter(subscription=subscription).all()
        self.assertEqual(len(payments), 1)

