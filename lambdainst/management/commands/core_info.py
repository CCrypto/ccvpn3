from django.core.management.base import BaseCommand

from lambdainst.core import core_api


class Command(BaseCommand):
    help = "Get informations about core API"

    def handle(self, *args, **options):
        for k, v in core_api.info.items():
            print("%s: %s" % (k, v))
