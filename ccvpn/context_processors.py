from django.conf import settings


def some_settings(request):
    return {
        'ROOT_URL': settings.ROOT_URL,
        'ADDITIONAL_HTML': settings.ADDITIONAL_HTML,
        'ADDITIONAL_HEADER_HTML': settings.ADDITIONAL_HEADER_HTML,
    }
