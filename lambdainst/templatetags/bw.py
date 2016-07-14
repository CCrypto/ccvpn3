from django.utils.translation import ugettext, ungettext
from django.template import Library
from django.utils.html import avoid_wrapping
from django.utils import formats

register = Library()


@register.filter(is_safe=True)
def bwformat(bps):
    try:
        bps = float(bps)
    except (TypeError, ValueError, UnicodeDecodeError):
        value = ungettext("%(bw)d bps", "%(bw)d bps", 0) % {'bw': 0}
        return avoid_wrapping(value)

    filesize_number_format = lambda value: formats.number_format(round(value, 1), -1)

    K = 1 * 10 ** 3
    M = 1 * 10 ** 6
    G = 1 * 10 ** 9
    T = 1 * 10 ** 12
    P = 1 * 10 ** 15

    if bps < K:
        value = ungettext("%(size)d bps", "%(size)d bps", bps) % {'size': bps}
    elif bps < M:
        value = ugettext("%s Kbps") % filesize_number_format(bps / K)
    elif bps < G:
        value = ugettext("%s Mbps") % filesize_number_format(bps / M)
    elif bps < T:
        value = ugettext("%s Gbps") % filesize_number_format(bps / G)
    elif bps < P:
        value = ugettext("%s Tbps") % filesize_number_format(bps / T)
    else:
        value = ugettext("%s Pbps") % filesize_number_format(bps / P)

    return avoid_wrapping(value)
