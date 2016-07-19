import asyncio
from decimal import Decimal as D

from django.conf import settings

from absortium.client import get_absortium_client
from core.utils.logging import getPrettyLogger
from poloniex.app import Application
from poloniexbot import constants
from poloniexbot.utils import update_storage, synchronize_orders, filter_orders, get_locked_balance, cut_off_orders, \
    create_actions, convert

__author__ = "andrew.shvv@gmail.com"

logger = getPrettyLogger(__name__)

client = get_absortium_client(api_key=settings.ABSORTIUM_API_KEY,
                              api_secret=settings.ABSORTIUM_API_SECRET,
                              base_api_uri="http://docker.backend:3000")

storage = {
    'orders': {
        'sell': [],
        'buy': []
    }
}


class PoloniexApp(Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def updates_handler(**update):
        if update.get('type') in [constants.POLONIEX_ORDER_REMOVED, constants.POLONIEX_ORDER_MODIFIED]:
            order = update.get("data")
            order["pair"] = update.get("currency_pair")

            order = convert(order)
            update_storage(storage, order)

    async def main(self):
        logger.debug("--" * 20 + "Cancel" + "--" * 20)
        for order in [order for order in client.orders.list() if order['status'] not in ['canceled', 'completed']]:
            logger.debug(client.orders.cancel(pk=order['pk']))

        # 1. Turn on Poloniex orders update.
        self.push_api.subscribe(topic=constants.CURRENCY_PAIR, handler=PoloniexApp.updates_handler)

        # 2. Get Poloniex orders.
        orders = await self.public_api.returnOrderBook(currencyPair=constants.CURRENCY_PAIR, depth=constants.COUNT)

        # 3. Merge Poloniex orders.
        synchronize_orders(storage, orders)

        # Every 5 second:
        while True:

            order_type = 'sell'
            from_currency = 'eth'
            to_currency = 'btc'

            # 1. Get Absortium orders.
            absortium_orders = client.orders.list(order_type=order_type)

            # 2. Leave only 'init' and 'pending' orders.
            absortium_orders = filter_orders(absortium_orders)

            # 3. Calculate how many amount we have to operate with. We should take into account money
            # restriction (Not all order from Poloniex will be synced, because we do not have such amount of money)
            account = client.accounts.retrieve(currency=from_currency)
            accounts_balance = D(account['amount'])
            amount = get_locked_balance(absortium_orders) + accounts_balance

            logger.debug("--" * 20 + "Account" + "--" * 20)
            logger.debug(account)

            # 4. Get Poloniex orders and cut off redundant.
            poloniex_orders = storage['orders'][order_type]

            logger.debug("--" * 20 + "Before cut" + "--" * 20)
            logger.debug(poloniex_orders)

            poloniex_orders = cut_off_orders(amount, poloniex_orders)

            logger.debug("--" * 20 + "After cut" + "--" * 20)
            logger.debug(poloniex_orders)

            # 5. What should have to do to sync the orders?
            actions = create_actions(absortium_orders, poloniex_orders)

            logger.debug("--" * 20 + "Actions" + "--" * 20)
            for order in actions['delete']:
                logger.debug({'delete': order})
                client.orders.cancel(**order)

            for order in actions['update']:
                del order['total']

                logger.debug({'update': order})
                client.orders.update(**order)

            for order in actions['create']:
                logger.debug({'create': order})
                client.orders.create(**order)

            await asyncio.sleep(0.5)
