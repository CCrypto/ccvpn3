import os.path

import markdown
from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.conf import settings
from django.utils.translation import ugettext as _, get_language
from django import http
from django.utils.http import is_safe_url
from django.utils.translation import (
    LANGUAGE_SESSION_KEY, check_for_language,
)


md = markdown.Markdown(extensions=['toc', 'meta', 'codehilite(noclasses=True)'])


def index(request):
    eur = '%.2f' % (settings.PAYMENTS_MONTHLY_PRICE / 100)
    return render(request, 'ccvpn/index.html', dict(eur_price=eur))


def chat(request):
    if request.user.is_authenticated():
        username = request.user.username + '|cc'
    else:
        username = "cc?"
    ctx = dict(username=username, title=_("Live Chat"))
    return render(request, 'ccvpn/chat.html', ctx)


def set_lang(request):
    """ django.views.i18n.set_language() with GET """

    next = request.GET.get('next', request.GET.get('next'))
    if not is_safe_url(url=next, host=request.get_host()):
        next = request.META.get('HTTP_REFERER')
        if not is_safe_url(url=next, host=request.get_host()):
            next = '/'
    response = http.HttpResponseRedirect(next)
    lang_code = request.GET.get('lang', None)
    if lang_code and check_for_language(lang_code):
        if hasattr(request, 'session'):
            request.session[LANGUAGE_SESSION_KEY] = lang_code
        else:
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code,
                                max_age=settings.LANGUAGE_COOKIE_AGE,
                                path=settings.LANGUAGE_COOKIE_PATH,
                                domain=settings.LANGUAGE_COOKIE_DOMAIN)
    return response


def page(request, name):
    basename = settings.PAGES_DIR + '/' + name

    username = request.user.username

    page_replace = {
        'USERNAME': username or '[username]',
    }

    files = [
        basename + '.' + get_language() + '.md',
        basename + '.en.md',
        basename + '.md',
    ]

    for file in files:
        if not os.path.isfile(file):
            continue

        with open(file, encoding='utf8') as fh:
            page = fh.read()
            for s, r in page_replace.items():
                page = page.replace('{' + s + '}', r)
            page = md.convert(page)

            title = md.Meta.get('title', [None])[0]
            ctx = dict(content=page, title=title)
            return render(request, 'ccvpn/page.html', ctx)

    return HttpResponseNotFound()

