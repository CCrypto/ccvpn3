from django.conf import settings


def get_client_ip(request):
    header_name = settings.REAL_IP_HEADER_NAME

    print(header_name)
    print(request.META)
    if header_name:
        header_name = header_name.replace('-', '_').upper()
        value = request.META.get('HTTP_' + header_name)
        if value:
            return value.split(',', 1)[0]

    return request.META.get('REMOTE_ADDR')
