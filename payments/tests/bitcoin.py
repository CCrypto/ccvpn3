from datetime import timedelta

from django.test import TestCase
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User

from payments.models import Payment
from payments.backends import BitcoinBackend

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


