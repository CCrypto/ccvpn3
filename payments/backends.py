import json
from ipaddress import IPv4Address, IPv4Network
from decimal import Decimal

from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from urllib.parse import urlencode
from urllib.request import urlopen
from django.core.urlresolvers import reverse
from django.conf import settings as project_settings


class BackendBase:
    backend_id = None
    backend_verbose_name = ""
    backend_display_name = ""
    backend_enabled = False

    def __init__(self, settings):
        pass

    def new_payment(self, payment):
        """ Initialize a payment and returns an URL to redirect the user.
        Can return a HTML string that will be sent back to the user in a
        default template (like a form) or a HTTP response (like a redirect).
        """
        raise NotImplementedError()

    def callback(self, payment, request):
        """ Handle a callback """
        raise NotImplementedError()

    def get_info(self):
        """ Returns some status (key, value) list """
        return ()

    def get_ext_url(self, payment):
        """ Returns URL to external payment view, or None """
        return None


class BitcoinBackend(BackendBase):
    """ Bitcoin backend.
    Connects to a bitcoind.
    """
    backend_id = 'bitcoin'
    backend_verbose_name = _("Bitcoin")
    backend_display_name = _("Bitcoin")

    COIN = 100000000

    def __init__(self, settings):
        from bitcoin import SelectParams
        from bitcoin.rpc import Proxy

        self.btc_value = settings.get('BITCOIN_VALUE')
        self.account = settings.get('ACCOUNT', 'ccvpn3')

        chain = settings.get('CHAIN')
        if chain:
            SelectParams(chain)

        self.url = settings.get('URL')
        if not self.url:
            return

        assert isinstance(self.btc_value, int)

        self.make_rpc = lambda: Proxy(self.url)
        self.rpc = self.make_rpc()
        self.backend_enabled = True

    def new_payment(self, payment):
        rpc = self.make_rpc()

        # bitcoins amount = (amount in cents) / (cents per bitcoin)
        btc_price = round(Decimal(payment.amount) / self.btc_value, 5)

        address = str(rpc.getnewaddress(self.account))

        msg = _("Please send %(amount)s BTC to %(address)s")
        payment.status_message = msg % dict(amount=str(btc_price), address=address)
        payment.backend_extid = address
        payment.backend_data = dict(btc_price=str(btc_price), btc_address=address)
        payment.save()
        return redirect(reverse('payments:view', args=(payment.id,)))

    def check(self, payment):
        rpc = self.make_rpc()

        if payment.status != 'new':
            return

        btc_price = payment.backend_data.get('btc_price')
        address = payment.backend_data.get('btc_address')
        if not btc_price or not address:
            return

        btc_price = Decimal(btc_price)

        received = Decimal(rpc.getreceivedbyaddress(address)) / self.COIN
        payment.paid_amount = int(received * self.btc_value)
        payment.backend_data['btc_paid_price'] = str(received)

        if received >= btc_price:
            payment.user.vpnuser.add_paid_time(payment.time)
            payment.user.vpnuser.on_payment_confirmed(payment)
            payment.user.vpnuser.save()

            payment.status = 'confirmed'

        payment.save()

    def get_info(self):
        rpc = self.make_rpc()

        try:
            info = rpc.getinfo()
            if not info:
                return [(_("Status"), "Error: got None")]
        except Exception as e:
            return [(_("Status"), "Error: " + repr(e))]
        v = info.get('version', 0)
        return (
            (_("Bitcoin value"), "%.2f €" % (self.btc_value / 100)),
            (_("Testnet"), info['testnet']),
            (_("Balance"), '{:f}'.format(info['balance'] / self.COIN)),
            (_("Blocks"), info['blocks']),
            (_("Bitcoind version"), '.'.join(str(v // 10 ** (2 * i) % 10 ** (2 * i))
                                             for i in range(3, -1, -1))),
        )

    def get_ext_url(self, payment):
        if not payment.backend_extid:
            return None
        return 'http://blockr.io/address/info/%s' % payment.backend_extid


class ManualBackend(BackendBase):
    """ Manual backend used to store and display informations about a
    payment processed manually.
    More a placeholder than an actual payment beckend, everything raises
    NotImplementedError().
    """

    backend_id = 'manual'
    backend_verbose_name = _("Manual")


class PaypalBackend(BackendBase):
    backend_id = 'paypal'
    backend_verbose_name = _("PayPal")
    backend_display_name = _("PayPal")

    def __init__(self, settings):
        self.test = settings.get('TEST', False)
        self.header_image = settings.get('HEADER_IMAGE', None)
        self.title = settings.get('TITLE', 'VPN Payment')
        self.currency = settings.get('CURRENCY', 'EUR')
        self.account_address = settings.get('ADDRESS')
        self.receiver_address = settings.get('RECEIVER', self.account_address)

        if self.test:
            default_api = 'https://www.sandbox.paypal.com/'
        else:
            default_api = 'https://www.paypal.com/'
        self.api_base = settings.get('API_BASE', default_api)

        if self.account_address:
            self.backend_enabled = True

    def new_payment(self, payment):
        ROOT_URL = project_settings.ROOT_URL
        params = {
            'cmd': '_xclick',
            'notify_url': ROOT_URL + reverse('payments:cb_paypal', args=(payment.id,)),
            'item_name': self.title,
            'amount': '%.2f' % (payment.amount / 100),
            'currency_code': self.currency,
            'business': self.account_address,
            'no_shipping': '1',
            'return': ROOT_URL + reverse('payments:view', args=(payment.id,)),
            'cancel_return': ROOT_URL + reverse('payments:cancel', args=(payment.id,)),
        }

        if self.header_image:
            params['cpp_header_image'] = self.header_image

        payment.status_message = _("Waiting for PayPal to confirm the transaction... It can take up to a few minutes...")
        payment.save()

        return redirect(self.api_base + '/cgi-bin/webscr?' + urlencode(params))

    def handle_verified_callback(self, payment, params):
        if self.test and params['test_ipn'] != '1':
            raise ValueError('Test IPN')

        txn_type = params.get('txn_type')
        if txn_type not in (None, 'web_accept', 'express_checkout'):
            # Not handled here and can be ignored
            return

        if params['payment_status'] == 'Refunded':
            payment.status = 'refunded'
            payment.status_message = None

        elif params['payment_status'] == 'Completed':
            if self.receiver_address != params['receiver_email']:
                raise ValueError('Wrong receiver: ' + params['receiver_email'])
            if self.currency.lower() != params['mc_currency'].lower():
                raise ValueError('Wrong currency: ' + params['mc_currency'])

            payment.paid_amount = int(float(params['mc_gross']) * 100)
            if payment.paid_amount < payment.amount:
                raise ValueError('Not fully paid.')

            payment.user.vpnuser.add_paid_time(payment.time)
            payment.user.vpnuser.on_payment_confirmed(payment)
            payment.user.vpnuser.save()

            payment.backend_extid = params['txn_id']
            payment.status = 'confirmed'
            payment.status_message = None
            payment.save()

    def verify_ipn(self, payment, request):
        v_url = self.api_base + '/cgi-bin/webscr?cmd=_notify-validate'
        v_req = urlopen(v_url, data=request.body, timeout=5)
        v_res = v_req.read()
        return v_res == b'VERIFIED'

    def callback(self, payment, request):
        if not self.verify_ipn(payment, request):
            return False

        params = request.POST

        try:
            self.handle_verified_callback(payment, params)
            return True
        except (KeyError, ValueError) as e:
            payment.status = 'error'
            payment.status_message = None
            payment.backend_data['ipn_exception'] = repr(e)
            payment.backend_data['ipn_last_data'] = repr(request.POST)
            payment.save()
            raise

    def get_ext_url(self, payment):
        if not payment.backend_extid:
            return None
        url = 'https://history.paypal.com/webscr?cmd=_history-details-from-hub&id=%s'
        return url % payment.backend_extid


class StripeBackend(BackendBase):
    backend_id = 'stripe'
    backend_verbose_name = _("Stripe")
    backend_display_name = _("Credit Card or Alipay (Stripe)")

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

    def get_ext_url(self, payment):
        if not payment.backend_extid:
            return None
        return 'https://dashboard.stripe.com/payments/%s' % payment.backend_extid


class CoinbaseBackend(BackendBase):
    backend_id = 'coinbase'
    backend_verbose_name = _("Coinbase")
    backend_display_name = _("Bitcoin with CoinBase")

    def __init__(self, settings):
        self.sandbox = settings.get('SANDBOX', False)
        if self.sandbox:
            default_site = 'https://sandbox.coinbase.com/'
            default_base = 'https://api.sandbox.coinbase.com/'
        else:
            default_site = 'https://www.coinbase.com/'
            default_base = 'https://api.coinbase.com/'

        self.currency = settings.get('CURRENCY', 'EUR')
        self.key = settings.get('KEY')
        self.secret = settings.get('SECRET')
        self.base = settings.get('BASE_URL', default_base)
        self.site = settings.get('SITE_URL', default_site)

        self.callback_secret = settings.get('CALLBACK_SECRET')
        self.callback_source_ip = settings.get('CALLBACK_SOURCE', '54.175.255.192/27')

        if not self.key or not self.secret or not self.callback_secret:
            return

        from coinbase.wallet.client import Client
        self.client = Client(self.key, self.secret, self.base)
        self.backend_enabled = True

    def new_payment(self, payment):
        ROOT_URL = project_settings.ROOT_URL

        months = int(payment.time.days / 30)
        username = payment.user.username

        amount_str = '%.2f' % (payment.amount / 100)
        name = "%d months for %s" % (months, username)
        checkout = self.client.create_checkout(
            amount=amount_str,
            currency=self.currency,
            name=name,
            success_url=ROOT_URL + reverse('payments:view', args=(payment.id,)),
            cancel_url=ROOT_URL + reverse('payments:cancel', args=(payment.id,)),
            metadata={'payment_id': payment.id},
        )
        embed_id = checkout['embed_code']
        payment.backend_data['checkout_id'] = checkout['id']
        payment.backend_data['embed_code'] = checkout['embed_code']
        return redirect(self.site + 'checkouts/' + embed_id
                        + '?custom=' + str(payment.id))

    def callback(self, Payment, request):
        if self.callback_source_ip:
            if ('.' in request.META['REMOTE_ADDR']) != ('.' in self.callback_source_ip):
                print("source IP version")
                print(repr(request.META.get('REMOTE_ADDR')))
                print(repr(self.callback_source_ip))
                return False  # IPv6 TODO
            net = IPv4Network(self.callback_source_ip)
            if IPv4Address(request.META['REMOTE_ADDR']) not in net:
                print("source IP")
                return False

        secret = request.GET.get('secret')
        if secret != self.callback_secret:
            print("secret")
            return False

        data = json.loads(request.body.decode('utf-8'))
        order = data.get('order')

        if not order:
            # OK but we don't care
            print("order")
            return True

        id = order.get('custom')
        try:
            payment = Payment.objects.get(id=id)
        except Payment.DoesNotExist:
            # Wrong ID - Valid request, ignore
            print("wrong payment")
            return True

        button = order.get('button')
        if not button:
            # Wrong structure.
            print("button")
            return False

        payment.status = 'confirmed'
        payment.save()
        payment.user.vpnuser.add_paid_time(payment.time)
        payment.user.vpnuser.on_payment_confirmed(payment)
        payment.user.vpnuser.save()
        return True

