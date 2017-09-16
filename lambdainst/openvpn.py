import json
import uuid
from django.utils.translation import ugettext as _
from django.conf import settings


CA_CERT = settings.OPENVPN_CA

CONFIG_OS = (
    ('windows', _("Windows")),
    ('android', _("Android")),
    ('ubuntu', _("Ubuntu")),
    ('osx', _("OS X")),
    ('ios', _("iOS")),
    ('chromeos', _("Chrome OS")),
    ('freebox', _("Freebox")),
    ('other', _("Other / GNU/Linux")),
)

PROTOCOLS = (
    ('udp', _("UDP (default)")),
    ('tcp', _("TCP")),
    ('udpl', _("UDP (low MTU)")),
)


def _make_onc(username, name, hostname, port, protocol, http_proxy=None, ipv6=True):
    cert_id = '{%s}' % uuid.uuid4()
    vpn_id = '{%s}' % uuid.uuid4()

    openvpn_config = {
        'ServerCARef': cert_id,
        'ClientCertType': 'None',
        'CompLZO': 'true',
        'Port': port,
        'Proto': protocol,
        'ServerPollTimeout': 10,
        'NsCertType': 'server',
        'Username': username,
    }
    cert = {
        'GUID': cert_id,
        'Type': 'Authority',
        'X509': CA_CERT.strip(),
    }
    vpn = {
        'GUID': vpn_id,
        'Name': name,
        'Type': 'VPN',
        'VPN': {
            'Type': 'OpenVPN',
            'Host': hostname,
            'OpenVPN': openvpn_config,
        },
    }

    return json.dumps({
        'type': 'UnencryptedConfiguration',
        'Certificates': [cert],
        'NetworkConfigurations': [vpn],
    }, indent=2)


def make_config(username, gw_name, os, protocol, http_proxy=None, ipv6=True):

    use_frag = protocol == 'udpl' and os != 'ios'
    ipv6 = ipv6 and (os != 'freebox')
    http_proxy = http_proxy if protocol == 'tcp' else None
    resolvconf = os in ('ubuntu', 'other')

    openvpn_proto = {'udp': 'udp', 'udpl': 'udp', 'tcp': 'tcp'}
    openvpn_ports = {'udp': 1196,  'udpl': 1194,  'tcp': 443}

    hostname = 'gw.%s.204vpn.net' % gw_name
    port = openvpn_ports[protocol]
    proto = openvpn_proto[protocol]

    if os == 'chromeos':
        name = "CCrypto VPN"
        if gw_name != 'random':
            name += " " + gw_name.upper()
        return _make_onc(username, name, hostname, port, proto, http_proxy, ipv6)

    remote = str(hostname)
    remote += ' ' + str(port)
    remote += ' ' + proto

    config = """\
# +----------------------------+
# | Cognitive Cryptography VPN |
# |  https://vpn.ccrypto.org/  |
# +----------------------------+

verb 4
client
tls-client
script-security 2
remote-cert-tls server
dev tun
nobind
persist-key
persist-tun
comp-lzo yes

remote {remote}

auth-user-pass

""".format(remote=remote)

    if os == 'ios':
        # i'd like to note here how much i hate OpenVPN
        config += "redirect-gateway ipv6\n"
        config += 'push "route 0.0.0.0 128.0.0.0"\n'
        config += 'push "route 128.0.0.0 128.0.0.0"\n'
    else:
        config += "redirect-gateway def1\n"
        if ipv6:
            config += "tun-ipv6\n"
            config += "route-ipv6 2000::/3\n"
            config += "\n"

    if use_frag:
        config += "fragment 1300\n"
        config += "mssfix 1300\n"
        config += "\n"

    if http_proxy:
        config += "http-proxy %s\n\n" % http_proxy

    if resolvconf:
        config += "up /etc/openvpn/update-resolv-conf\n"
        config += "down /etc/openvpn/update-resolv-conf\n"
        config += "\n"

    if os == 'windows':
        config += "register-dns\n"
        config += "\n"

    config += "<ca>\n%s\n</ca>" % CA_CERT

    if os == 'windows':
        config = config.replace('\n', '\r\n')

    return config



