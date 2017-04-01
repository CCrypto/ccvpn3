from datetime import datetime, timedelta
import re

from django.conf import settings
from .models import User


class ReferrerMiddleware():
    def process_request(self, request):
        if 'ref' in request.GET:
            id = request.GET['ref']
        elif 'referrer' in request.COOKIES:
            id = request.COOKIES['referrer']
        else:
            return

        try:
            id = int(id.strip())
        except (ValueError, TypeError):
            return

        try:
            u = User.objects.get(id=id)
        except User.DoesNotExist:
            return

        request.session['referrer'] = u.id

    def process_response(self, request, response):
        id = request.session.get('referrer')
        if not id:
            return response

        max_age = 365 * 24 * 60 * 60
        expires = (datetime.utcnow() + timedelta(seconds=max_age))
        expires = expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
        response.set_cookie('referrer', id,
                            max_age=max_age,
                            expires=expires,
                            domain=settings.SESSION_COOKIE_DOMAIN,
                            secure=settings.SESSION_COOKIE_SECURE or None)
        return response


class CampaignMiddleware():
    GET_FIELDS = ['pk_campaign', 'utm_campaign', 'utm_medium', 'utm_source']

    def _get_name(self, request):
        for f in self.GET_FIELDS:
            if f in request.GET and request.GET[f]:
                return request.GET[f]
        if 'campaign' in request.COOKIES:
            return request.COOKIES['campaign']
        return None

    def process_request(self, request):
        name = self._get_name(request)
        if not name:
            return

        name = name.strip()

        if len(name) >= 64 or not re.match('^[a-zA-Z0-9_.:-]+$', name):
            return

        request.session['campaign'] = name

    def process_response(self, request, response):
        name = request.session.get('campaign')
        if not name:
            return response

        max_age = 365 * 24 * 60 * 60
        expires = (datetime.utcnow() + timedelta(seconds=max_age))
        expires = expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
        response.set_cookie('campaign', name,
                            max_age=max_age,
                            expires=expires,
                            domain=settings.SESSION_COOKIE_DOMAIN,
                            secure=settings.SESSION_COOKIE_SECURE or None)
        return response
