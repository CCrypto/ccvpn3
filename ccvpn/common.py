from django.conf import settings
from constance import config
from datetime import timedelta


def get_client_ip(request):
    header_name = settings.REAL_IP_HEADER_NAME

    if header_name:
        header_name = header_name.replace('-', '_').upper()
        value = request.META.get('HTTP_' + header_name)
        if value:
            return value.split(',', 1)[0]

    return request.META.get('REMOTE_ADDR')


def get_price():
    return config.MONTHLY_PRICE_EUR


def get_price_float():
    return get_price() / 100


def get_trial_period_duration():
    return config.TRIAL_PERIOD_HOURS * timedelta(hours=1)


def parse_integer_list(ls):
    l = ls.split(',')
    l = [p.strip() for p in l]
    l = [p for p in l if p]
    l = [int(p) for p in l]
    return l

