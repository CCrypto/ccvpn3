import requests
import io
import zipfile
import hmac
import base64
from hashlib import sha256
from urllib.parse import urlencode, parse_qsl
from datetime import timedelta, datetime

from django.http import (
    HttpResponse, JsonResponse,
    HttpResponseRedirect,
    HttpResponseNotFound, HttpResponseForbidden
)
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.sites import site
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.conf import settings as project_settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.contrib import auth
from django.contrib.auth.models import User
from django_countries import countries
from constance import config as site_config
import lcoreapi

from ccvpn.common import get_client_ip, get_price_float
from payments.models import ACTIVE_BACKENDS
from .forms import SignupForm, ReqEmailForm
from .models import GiftCode, VPNUser
from .core import core_api
from . import core
from . import graphs
from . import openvpn


def get_locations():
    """ Pretty bad thing that returns get_locations() with translated stuff
    that depends on the request
    """
    countries_d = dict(countries)
    locations = core.get_locations()
    for k, v in locations:
        cc = v['country_code'].upper()
        v['country_name'] = countries_d.get(cc, cc)
    return locations


def ca_crt(request):
    return HttpResponse(content=project_settings.OPENVPN_CA,
                        content_type='application/x-x509-ca-cert')


def logout(request):
    auth.logout(request)
    return redirect('index')


def signup(request):
    if request.user.is_authenticated():
        return redirect('account:index')

    if request.method != 'POST':
        form = SignupForm()
        return render(request, 'ccvpn/signup.html', dict(form=form))

    form = SignupForm(request.POST)

    if not form.is_valid():
        return render(request, 'ccvpn/signup.html', dict(form=form))

    user = User.objects.create_user(form.cleaned_data['username'],
                                    form.cleaned_data['email'],
                                    form.cleaned_data['password'])
    user.save()

    if core.VPN_AUTH_STORAGE == 'core':
        core.create_user(form.cleaned_data['username'], form.cleaned_data['password'])

    try:
        user.vpnuser.referrer = User.objects.get(id=request.session.get('referrer'))
    except User.DoesNotExist:
        pass

    user.vpnuser.campaign = request.session.get('campaign')

    user.vpnuser.save()

    user.backend = 'django.contrib.auth.backends.ModelBackend'
    auth.login(request, user)

    return redirect('account:index')


@login_required
def discourse_login(request):
    sso_secret = project_settings.DISCOURSE_SECRET
    discourse_url = project_settings.DISCOURSE_URL

    if project_settings.DISCOURSE_SSO is not True:
        return HttpResponseNotFound()

    payload = request.GET.get('sso', '')
    signature = request.GET.get('sig', '')

    expected_signature = hmac.new(sso_secret.encode('utf-8'),
                                  payload.encode('utf-8'),
                                  sha256).hexdigest()

    if signature != expected_signature:
        return HttpResponseNotFound()

    if request.method == 'POST' and 'email' in request.POST:
        form = ReqEmailForm(request.POST)
        if not form.is_valid():
            return render(request, 'ccvpn/require_email.html', dict(form=form))

        request.user.email = form.cleaned_data['email']
        request.user.save()

    if not request.user.email:
        form = ReqEmailForm()
        return render(request, 'ccvpn/require_email.html', dict(form=form))

    try:
        payload = base64.b64decode(payload).decode('utf-8')
        payload_data = dict(parse_qsl(payload))
    except (TypeError, ValueError):
        return HttpResponseNotFound()

    payload_data.update({
        'external_id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'require_activation': 'true',
    })

    payload = urlencode(payload_data)
    payload = base64.b64encode(payload.encode('utf-8'))
    signature = hmac.new(sso_secret.encode('utf-8'), payload, sha256).hexdigest()
    redirect_query = urlencode(dict(sso=payload, sig=signature))
    redirect_path = '/session/sso_login?' + redirect_query

    return HttpResponseRedirect(discourse_url + redirect_path)


@login_required
def index(request):
    ref_url = project_settings.ROOT_URL + '?ref=' + str(request.user.id)

    twitter_url = 'https://twitter.com/intent/tweet?'
    twitter_args = {
        'text': _("Awesome VPN! 3€ per month, with a free 7 days trial!"),
        'via': 'CCrypto_VPN',
        'url': ref_url,
        'related': 'CCrypto_VPN,CCrypto_org'
    }

    class price_fn:
        """ Clever hack to get the price in templates with {{price.3}} with
        3 an arbitrary number of months
        """
        def __getitem__(self, months):
            n = int(months) * get_price_float()
            c = project_settings.PAYMENTS_CURRENCY[1]
            return '%.2f %s' % (n, c)

    context = dict(
        title=_("Account"),
        ref_url=ref_url,
        twitter_link=twitter_url + urlencode(twitter_args),
        subscription=request.user.vpnuser.get_subscription(include_unconfirmed=True),
        backends=sorted(ACTIVE_BACKENDS.values(), key=lambda x: x.backend_id),
        subscr_backends=sorted((b for b in ACTIVE_BACKENDS.values()
                                if b.backend_has_recurring),
                               key=lambda x: x.backend_id),
        default_backend='paypal',
        recaptcha_site_key=project_settings.RECAPTCHA_SITE_KEY,
        price=price_fn(),
        user_motd=site_config.MOTD_USER,
    )
    return render(request, 'lambdainst/account.html', context)


def captcha_test(grr, request):
    api_url = project_settings.RECAPTCHA_API

    if api_url == 'TEST' and grr == 'TEST-TOKEN':
        # FIXME: i'm sorry.
        return True

    data = dict(secret=project_settings.RECAPTCHA_SECRET_KEY,
                remoteip=get_client_ip(request),
                response=grr)

    try:
        r = requests.post(api_url, data=data)
        r.raise_for_status()
        d = r.json()
        return d.get('success')
    except (requests.ConnectionError, requests.HTTPError, ValueError):
        return False


@login_required
def trial(request):
    if request.method != 'POST' or not request.user.vpnuser.can_have_trial:
        return redirect('account:index')

    grr = request.POST.get('g-recaptcha-response', '')
    if captcha_test(grr, request):
        request.user.vpnuser.give_trial_period()
        request.user.vpnuser.save()
        messages.success(request, _("OK!"))
    else:
        messages.error(request, _("Invalid captcha"))

    return redirect('account:index')


@login_required
def settings(request):
    if request.method != 'POST':
        return render(request, 'lambdainst/settings.html')

    pw = request.POST.get('password')
    pw2 = request.POST.get('password2')
    if pw and pw2:
        if pw != pw2:
            messages.error(request, _("Passwords do not match"))
        else:
            request.user.set_password(pw)

            if core.VPN_AUTH_STORAGE == 'core':
                core.update_user_password(request.user, pw)

            messages.success(request, _("OK!"))

    email = request.POST.get('email')
    if email:
        request.user.email = email
    else:
        request.user.email = ''

    request.user.save()

    return render(request, 'lambdainst/settings.html', dict(title=_("Settings")))


@login_required
def gift_code(request):
    try:
        code = GiftCode.objects.get(code=request.POST.get('code', '').strip(), available=True)
    except GiftCode.DoesNotExist:
        code = None

    if code is None:
        messages.error(request, _("Gift code not found or already used."))
    elif not code.use_on(request.user):
        messages.error(request, _("Gift code only available to free accounts."))
    else:
        messages.success(request, _("OK!"))

    return redirect('account:index')


@login_required
def logs(request):
    page_size = 20
    page = int(request.GET.get('page', 0))
    offset = page * page_size

    base = core_api.info['current_instance']
    path = '/users/' + request.user.username + '/sessions/'
    try:
        l = core_api.get(base + path, offset=offset, limit=page_size)
        total_count = l['total_count']
        items = l['items']
    except lcoreapi.APINotFoundError:
        total_count = 0
        items = []
    return render(request, 'lambdainst/logs.html', {
        'sessions': items,
        'page': page,
        'prev': page - 1 if page > 0 else None,
        'next': page + 1 if offset + page_size < total_count else None,
        'last_page': total_count // page_size,
        'title': _("Logs"),
    })


@login_required
def config(request):
    return render(request, 'lambdainst/config.html', dict(
        title=_("Config"),
        config_os=openvpn.CONFIG_OS,
        config_countries=(c for _, c in get_locations()),
        config_protocols=openvpn.PROTOCOLS,
    ))


@login_required
def config_dl(request):
    allowed_cc = [cc for (cc, _) in get_locations()]

    os = request.GET.get('client_os')

    common_options = {
        'username': request.user.username,
        'protocol': request.GET.get('protocol'),
        'os': os,
        'http_proxy': request.GET.get('http_proxy'),
        'ipv6': 'enable_ipv6' in request.GET,
    }

    # Should be validated since it's used in the filename
    # other common options are only put in the config file
    protocol = common_options['protocol']
    if protocol not in ('udp', 'udpl', 'tcp'):
        return HttpResponseNotFound()

    location = request.GET.get('gateway')

    if location == 'all':
        # Multiple gateways in a zip archive

        f = io.BytesIO()
        z = zipfile.ZipFile(f, mode='w')

        for gw_name in allowed_cc + ['random']:
            if os == 'chromeos':
                filename = 'ccrypto-%s-%s.onc' % (gw_name, protocol)
            else:
                filename = 'ccrypto-%s-%s.ovpn' % (gw_name, protocol)
            config = openvpn.make_config(gw_name=gw_name, **common_options)
            z.writestr(filename, config.encode('utf-8'))

        z.close()

        r = HttpResponse(content=f.getvalue(), content_type='application/zip')
        r['Content-Disposition'] = 'attachment; filename="%s.zip"' % filename
        return r
    else:
        # Single gateway
        if location[3:] in allowed_cc:
            gw_name = location[3:]
        else:
            gw_name = 'random'
        if os == 'chromeos':
            filename = 'ccrypto-%s-%s.onc' % (gw_name, protocol)
        else:
            filename = 'ccrypto-%s-%s.ovpn' % (gw_name, protocol)

        config = openvpn.make_config(gw_name=gw_name, **common_options)

        if 'plain' in request.GET:
            return HttpResponse(content=config, content_type='text/plain')
        else:
            if os == 'chromeos':
                r = HttpResponse(content=config, content_type='application/x-onc')
            else:
                r = HttpResponse(content=config, content_type='application/x-openvpn-profile')
            r['Content-Disposition'] = 'attachment; filename="%s"' % filename
            return r


@csrf_exempt
def api_auth(request):
    if request.method != 'POST':
        return HttpResponseNotFound()

    if core.VPN_AUTH_STORAGE != 'inst':
        return HttpResponseNotFound()

    username = request.POST.get('username')
    password = request.POST.get('password')
    secret = request.POST.get('secret')

    if secret != core.LCORE_INST_SECRET:
        return HttpResponseForbidden(content="Invalid secret")

    user = authenticate(username=username, password=password)
    if not user or not user.is_active:
        return JsonResponse(dict(status='fail', message="Invalid credentials"))

    if not user.vpnuser.is_paid:
        return JsonResponse(dict(status='fail', message="Not allowed to connect"))

    user.vpnuser.last_vpn_auth = timezone.now()
    user.vpnuser.save()

    return JsonResponse(dict(status='ok'))


def api_locations(request):
    def format_loc(cc, l):
        msg = ' [%s]' % l['message'] if l['message'] else ''
        return {
            'country_name': l['country_name'] + msg,
            'country_code': cc,
            'hostname': l['hostname'],
            'bandwidth': l['bandwidth'],
            'servers': l['servers'],
        }
    return JsonResponse(dict(locations=[format_loc(cc, l) for cc, l in get_locations()]))


def status(request):
    locations = get_locations()

    ctx = {
        'title': _("Status"),
        'n_users': VPNUser.objects.filter(expiration__gte=timezone.now()).count(),
        'n_sess': core.current_active_sessions(),
        'n_gws': sum(l['servers'] for cc, l in locations),
        'n_countries': len(set(cc for cc, l in locations)),
        'total_bw': sum(l['bandwidth'] for cc, l in locations),
        'locations': locations,
    }
    return render(request, 'lambdainst/status.html', ctx)


@user_passes_test(lambda user: user.is_staff)
def admin_status(request):
    graph_name = request.GET.get('graph_name')
    graph_period = request.GET.get('period')
    if graph_period not in ('y', 'm'):
        graph_period = 'm'
    if graph_name:
        if graph_name == 'users':
            content = graphs.users_graph(graph_period)
        elif graph_name == 'payments_paid':
            content = graphs.payments_paid_graph(graph_period)
        elif graph_name == 'payments_success':
            content = graphs.payments_success_graph(graph_period)
        else:
            return HttpResponseNotFound()
        return HttpResponse(content=content, content_type='image/svg+xml')

    payment_status = ((b, b.get_info()) for b in ACTIVE_BACKENDS.values())
    payment_status = ((b, i) for (b, i) in payment_status if i)

    ctx = {
        'api_status': {k: str(v) for k, v in core_api.info.items()},
        'payment_backends': sorted(ACTIVE_BACKENDS.values(), key=lambda x: x.backend_id),
        'payment_status': payment_status,
    }
    ctx.update(site.each_context(request))
    return render(request, 'lambdainst/admin_status.html', ctx)


@user_passes_test(lambda user: user.is_staff)
def admin_ref(request):
    last_week = datetime.now() - timedelta(days=7)
    last_month = datetime.now() - timedelta(days=30)

    top_ref = User.objects.annotate(n_ref=Count('referrals')).order_by('-n_ref')[:10]
    top_ref_week = User.objects.filter(referrals__user__date_joined__gt=last_week) \
                               .annotate(n_ref=Count('referrals')) \
                               .order_by('-n_ref')[:10]
    top_ref_month = User.objects.filter(referrals__user__date_joined__gt=last_month) \
                                .annotate(n_ref=Count('referrals')) \
                                .order_by('-n_ref')[:10]

    ctx = {
        'top_ref': top_ref,
        'top_ref_week': top_ref_week,
        'top_ref_month': top_ref_month,
    }
    ctx.update(site.each_context(request))
    return render(request, 'lambdainst/admin_ref.html', ctx)





