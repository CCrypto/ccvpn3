from decimal import Decimal

from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from .base import BackendBase


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


