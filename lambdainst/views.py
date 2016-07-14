import requests
import io
import zipfile
from urllib.parse import urlencode
from datetime import timedelta, datetime

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from django.http import JsonResponse
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

from payments.models import ACTIVE_BACKENDS
from .forms import SignupForm
from .models import GiftCode, VPNUser
from .core import core_api, current_active_sessions, get_locations as core_get_locations
from .core import LCORE_INST_SECRET, LCORE_SOURCE_ADDR
from . import graphs
from . import openvpn


def get_locations():
    """ Pretty bad thing that returns get_locations() with translated stuff
    that depends on the request
    """
    countries_d = dict(countries)
    locations = core_get_locations()
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

    try:
        user.vpnuser.referrer = User.objects.get(id=request.session.get('referrer'))
    except User.DoesNotExist:
        pass

    user.vpnuser.save()

    user.backend = 'django.contrib.auth.backends.ModelBackend'
    auth.login(request, user)

    return redirect('account:index')


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

    context = dict(
        title=_("Account"),
        ref_url=ref_url,
        twitter_link=twitter_url + urlencode(twitter_args),
        backends=sorted(ACTIVE_BACKENDS.values(), key=lambda x: x.backend_id),
        default_backend='paypal',
        recaptcha_site_key=project_settings.RECAPTCHA_SITE_KEY,
    )
    return render(request, 'lambdainst/account.html', context)


def captcha_test(grr, request):
    api_url = project_settings.RECAPTCHA_API

    if api_url == 'TEST' and grr == 'TEST-TOKEN':
        # FIXME: i'm sorry.
        return True

    data = dict(secret=project_settings.RECAPTCHA_SECRET_KEY,
                remoteip=request.META['REMOTE_ADDR'],
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
    l = core_api.get(base + path, offset=offset, limit=page_size)
    return render(request, 'lambdainst/logs.html', {
        'sessions': l['items'],
        'page': page,
        'prev': page - 1 if page > 0 else None,
        'next': page + 1 if offset + page_size < l['total_count'] else None,
        'last_page': l['total_count'] // page_size,
        'title': _("Logs"),
    })


@login_required
def config(request):
    return render(request, 'lambdainst/config.html', dict(
        titla=_("Config"),
        config_os=openvpn.CONFIG_OS,
        config_countries=(c for _, c in get_locations()),
        config_protocols=openvpn.PROTOCOLS,
    ))


@login_required
def config_dl(request):
    allowed_cc = [cc for (cc, _) in get_locations()]

    common_options = {
        'protocol': request.GET.get('protocol'),
        'os': request.GET.get('client_os'),
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
        filename = 'ccrypto-%s-%s.ovpn' % (gw_name, protocol)

        config = openvpn.make_config(gw_name=gw_name, **common_options)

        if 'plain' in request.GET:
            return HttpResponse(content=config, content_type='text/plain')
        else:
            r = HttpResponse(content=config, content_type='application/x-openvpn-profile')
            r['Content-Disposition'] = 'attachment; filename="%s.ovpn"' % filename
            return r


@csrf_exempt
def api_auth(request):
    if request.method != 'POST':
        return HttpResponseNotFound()

    username = request.POST.get('username')
    password = request.POST.get('password')
    secret = request.POST.get('secret')

    if secret != LCORE_INST_SECRET:
        return HttpResponseForbidden(content="Invalid secret")

    user = authenticate(username=username, password=password)
    if not user or not user.is_active:
        return JsonResponse(dict(status='fail', message="Invalid credentials"))

    if not user.vpnuser.is_paid:
        return JsonResponse(dict(status='fail', message="Not allowed to connect"))

    user.vpnuser.last_vpn_auth = timezone.now()
    user.vpnuser.save()

    return JsonResponse(dict(status='ok'))


def status(request):
    locations = get_locations()

    ctx = {
        'title': _("Status"),
        'n_users': VPNUser.objects.filter(expiration__gte=timezone.now()).count(),
        'n_sess': current_active_sessions(),
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





