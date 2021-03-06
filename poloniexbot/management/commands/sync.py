from django.conf import settings
from django.core.management.base import BaseCommand

from poloniexbot.main import PoloniexApp

__author__ = 'andrew.shvv@gmail.com'


class Command(BaseCommand):
    help = 'Sync Poloniex orders and create Absortium orders'

    def handle(self, *args, **options):
        app = PoloniexApp(api_key=settings.POLONIEX_API_KEY, api_sec=settings.POLONIEX_API_SECRET)
        app.run()
