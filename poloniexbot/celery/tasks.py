from decimal import Decimal as D

from celery import shared_task
from django.conf import settings
from django.db import IntegrityError, transaction
from requests.exceptions import ConnectionError, ConnectTimeout

from absortium.client import Client
from poloniex.app import SyncApp
from poloniexbot import constants
from poloniexbot.celery.base import get_base_class
from poloniexbot.error import PoloniexBotError
from poloniexbot.models import Redirect, Transmission


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES, base=get_base_class())
def process_redirect(self, **kwargs):
    def get_status(order, trades):
        poloniex_amount = sum([D(trade["amount"]) for trade in trades])
        absortium_amount = D(order["amount"])

        if poloniex_amount == absortium_amount:
            return constants.REDIRECT_APPROVING
        else:
            return constants.REDIRECT_PENDING

    def send_poloniex_order(order):
        if order["type"] == "buy":
            return poloniex_api.trading.buy(currency_pair=order["pair"],
                                            rate=order["price"],
                                            amount=order["amount"])
        elif order["type"] == "sell":
            return poloniex_api.trading.sell(currency_pair=order["pair"],
                                             rate=order["price"],
                                             amount=order["amount"])

    try:
        absortium_api = Client(api_key=settings.ABSORTIUM_API_KEY,
                               api_secret=settings.ABSORTIUM_API_SECRET,
                               base_api_uri=constants.BACKEND_URL)

        poloniex_api = SyncApp(api_key=settings.API_KEY,
                               api_sec=settings.API_SECRET)

        redirect = Redirect.objects.get(pk=kwargs["redirect_pk"])
        order = absortium_api.orders.retrieve(pk=redirect.absortium_order_pk)

        if redirect.status == constants.REDIRECT_INIT:
            with transaction.atomic():
                response = send_poloniex_order(order)
                redirect.poloniex_order_pk = response["orderNumber"]

                trades = response["resultingTrades"]
                redirect.status = get_status(order, trades)
                redirect.save()

        if redirect.status == constants.REDIRECT_PENDING:
            with transaction.atomic():
                trades = poloniex_api.trading.returnOrderTrades(order_number=redirect.poloniex_order_pk)
                redirect.status = get_status(order, trades)
                redirect.save()

        if redirect.status == constants.REDIRECT_APPROVING:
            with transaction.atomic():
                # TODO: If exception ApproveFailed was raised than it means that this order was abandoned (canceled) by user in Absortium system.

                order = absortium_api.orders.approve(pk=redirect.absortium_order_pk)
                redirect.status = constants.REDIRECT_TRANSMISSION
                redirect.save()

        if redirect.status == constants.REDIRECT_TRANSMISSION:
            with transaction.atomic():

                if order["type"] == "sell":
                    transmit_money(currency="eth",
                                   amount=order["amount"],
                                   system=constants.SYSTEM_ABSORTIUM,
                                   redirect_id=redirect.pk)
                    transmit_money(currency="btc",
                                   amount=order["total"],
                                   system=constants.SYSTEM_POLONIEX,
                                   redirect_id=redirect.pk)
                elif order["type"] == "buy":
                    transmit_money(currency="btc",
                                   amount=order["total"],
                                   system=constants.SYSTEM_ABSORTIUM,
                                   redirect_id=redirect.pk)
                    transmit_money(currency="eth",
                                   amount=order["amount"],
                                   system=constants.SYSTEM_POLONIEX,
                                   redirect_id=redirect.pk)

                redirect.status = constants.REDIRECT_COMPLETED
                redirect.save()

    except IntegrityError:
        """
            Redirect was already created in another task.
        """
        pass

    except (ConnectionError, ConnectTimeout) as e:
        raise self.retry(countdown=constants.RETRY_COUNTDOWN)


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES, base=get_base_class())
def transmit_money(self, currency, amount, system, redirect_id):
    try:
        with transaction.atomic():
            if system not in constants.AVAILABLE_SYSTEMS:
                raise PoloniexBotError("Unknown system '{}'".format(system))

            if system == constants.SYSTEM_ABSORTIUM:
                absortium_api = Client(api_key=settings.ABSORTIUM_API_KEY,
                                api_secret=settings.ABSORTIUM_API_SECRET,
                                base_api_uri=constants.BACKEND_URL)
                absortium_api.withdrawals.create(amount=amount, address=settings.ADDRESS_POLONIEX, currency=currency)

            elif system == constants.SYSTEM_POLONIEX:
                poloniex_api = SyncApp(api_key=settings.API_KEY,
                                 api_sec=settings.API_SECRET)
                poloniex_api.trading.witdrawal(amount=amount, address=settings.ADDRESS_ABSORTIUM, currency=currency)

            t = Transmission(amount=amount, currency=currency, system=system, redirect_id=redirect_id)
            t.save()

    except (ConnectionError, ConnectTimeout) as e:
        raise self.retry(countdown=constants.RETRY_COUNTDOWN)
