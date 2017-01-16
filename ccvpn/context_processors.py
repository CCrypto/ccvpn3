from django.conf import settings
from ccvpn.common import get_client_ip
from lambdainst.core import is_vpn_gateway


def some_settings(request):
    client_ip = get_client_ip(request)
    return {
        'CLIENT_IP': client_ip,
        'CLIENT_ON_VPN': is_vpn_gateway(client_ip),
        'ROOT_URL': settings.ROOT_URL,
        'ADDITIONAL_HTML': settings.ADDITIONAL_HTML,
        'ADDITIONAL_HEADER_HTML': settings.ADDITIONAL_HEADER_HTML,
    }
