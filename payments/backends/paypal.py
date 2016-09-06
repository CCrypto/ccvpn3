from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from urllib.parse import urlencode
from urllib.request import urlopen
from django.core.urlresolvers import reverse
from django.conf import settings as project_settings

from .base import BackendBase


class PaypalBackend(BackendBase):
    backend_id = 'paypal'
    backend_verbose_name = _("PayPal")
    backend_display_name = _("PayPal")
    backend_has_recurring = True

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

        payment.status_message = _("Waiting for PayPal to confirm the transaction... " +
                                   "It can take up to a few minutes...")
        payment.save()

        return redirect(self.api_base + '/cgi-bin/webscr?' + urlencode(params))

    def new_subscription(self, rps):
        months = {
            '3m': 3,
            '6m': 6,
            '12m': 12,
        }[rps.period]

        ROOT_URL = project_settings.ROOT_URL
        params = {
            'cmd': '_xclick-subscriptions',
            'notify_url': ROOT_URL + reverse('payments:cb_paypal_subscr', args=(rps.id,)),
            'item_name': self.title,
            'currency_code': self.currency,
            'business': self.account_address,
            'no_shipping': '1',
            'return': ROOT_URL + reverse('payments:return_subscr', args=(rps.id,)),
            'cancel_return': ROOT_URL + reverse('account:index'),

            'a3': '%.2f' % (rps.period_amount / 100),
            'p3': str(months),
            't3': 'M',
            'src': '1',
        }

        if self.header_image:
            params['cpp_header_image'] = self.header_image

        rps.save()

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
            self.handle_completed_payment(payment, params)

    def handle_verified_callback_subscr(self, subscr, params):
        if self.test and params['test_ipn'] != '1':
            raise ValueError('Test IPN')

        txn_type = params.get('txn_type')
        if not txn_type.startswith('subscr_'):
            # Not handled here and can be ignored
            return

        if txn_type == 'subscr_payment':
            if params['payment_status'] == 'Refunded':
                # FIXME: Find the payment and do something
                pass

            elif params['payment_status'] == 'Completed':
                payment = subscr.create_payment()
                if not self.handle_completed_payment(payment, params):
                    return

                subscr.last_confirmed_payment = payment.created
                subscr.backend_extid = params.get('subscr_id', '')
                if subscr.status == 'new' or subscr.status == 'unconfirmed':
                    subscr.status = 'active'
                subscr.save()
        elif txn_type == 'subscr_cancel' or txn_type == 'subscr_eot':
            subscr.status = 'cancelled'
            subscr.save()

    def handle_completed_payment(self, payment, params):
        from payments.models import Payment

        # Prevent making duplicate Payments if IPN is received twice
        pc = Payment.objects.filter(backend_extid=params['txn_id']).count()
        if pc > 0:
            return False

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
        return True

    def verify_ipn(self, request):
        v_url = self.api_base + '/cgi-bin/webscr?cmd=_notify-validate'
        v_req = urlopen(v_url, data=request.body, timeout=5)
        v_res = v_req.read()
        return v_res == b'VERIFIED'

    def callback(self, payment, request):
        if not self.verify_ipn(request):
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

    def callback_subscr(self, subscr, request):
        if not self.verify_ipn(request):
            return False

        params = request.POST

        try:
            self.handle_verified_callback_subscr(subscr, params)
            return True
        except (KeyError, ValueError) as e:
            subscr.status = 'error'
            subscr.status_message = None
            subscr.backend_data['ipn_exception'] = repr(e)
            subscr.backend_data['ipn_last_data'] = repr(request.POST)
            subscr.save()
            raise

    def get_ext_url(self, payment):
        if not payment.backend_extid:
            return None
        url = 'https://history.paypal.com/webscr?cmd=_history-details-from-hub&id=%s'
        return url % payment.backend_extid

