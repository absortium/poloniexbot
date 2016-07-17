__author__ = 'andrew.shvv@gmail.com'

from django.apps import AppConfig


class PoloniexBotConfig(AppConfig):
    name = 'poloniexbot'
    verbose_name = "Poloniexbot"

    def ready(self):
        super(PoloniexBotConfig, self).ready()
