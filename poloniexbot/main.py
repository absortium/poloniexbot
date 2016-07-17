from decimal import Decimal

from core.utils.logging import getPrettyLogger
from poloniex.app import Application
from poloniexbot import constants

__author__ = "andrew.shvv@gmail.com"

logger = getPrettyLogger(__name__)

CURRENCY_PAIR = "BTC_ETH"
COUNT = 20


def convert(order):
    price = Decimal(order["rate"])
    amount = Decimal(order.get("amount", 0))

    if order["type"] in ["bid", "bids"]:
        offer_type = "buy"
    elif order["type"] in ["ask", "asks"]:
        offer_type = "sell"
    else:
        raise Exception("Unknown order type")

    return {
        "pair": order["pair"].lower(),
        "type": offer_type,
        "price": price,
        "amount": amount,
        "need_approve": True
    }


class PoloniexApp(Application):
    @staticmethod
    def updates_handler(**update):
        if update.get('type') in [constants.POLONIEX_OFFER_REMOVED, constants.POLONIEX_OFFER_MODIFIED]:
            order = update.get("data")
            order["pair"] = update.get("currency_pair")

            order = convert(order)

    @staticmethod
    def synchronize_orders(orders):
        def sync(orders, _type):
            for price, amount in orders[_type]:
                order = {
                    "rate": price,
                    "amount": amount,
                    "pair": CURRENCY_PAIR,
                    "type": _type
                }

                order = convert(order)
                # safe_offer_update(price=offer["price"],
                #                   pair=offer["pair"],
                #                   order_type=offer["type"],
                #                   system=offer["system"],
                #                   update=lambda *args: offer["amount"])

        sync(orders, "bids")
        sync(orders, "asks")

    async def main(self):

        # Subscribe on order update to keep offers synchronized with Poloniex.
        self.push_api.subscribe(topic=CURRENCY_PAIR, handler=PoloniexApp.updates_handler)

        # Download all Poloniex orders; convert them to offers; add them to the system.
        orders = await self.public_api.returnOrderBook(currencyPair=CURRENCY_PAIR, depth=COUNT)
        PoloniexApp.synchronize_orders(orders)
