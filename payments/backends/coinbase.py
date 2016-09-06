import json
from ipaddress import IPv4Address, IPv4Network

from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.conf import settings as project_settings

from .base import BackendBase


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
        return redirect(self.site + 'checkouts/' + embed_id +
                        '?custom=' + str(payment.id))

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


