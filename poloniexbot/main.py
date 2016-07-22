import asyncio
import signal
import sys
from decimal import Decimal as D

from django.conf import settings

from absortium.client import get_absortium_client
from core.utils.logging import getPrettyLogger
from poloniex.app import Application
from poloniexbot import constants
from poloniexbot.utils import \
    update_storage, \
    synchronize_orders, \
    filter_orders, \
    get_locked_balance, \
    cut_off_orders, \
    create_actions, \
    convert, \
    apply_action, \
    get_from_currency, \
    create_poloniex_orders

__author__ = "andrew.shvv@gmail.com"

logger = getPrettyLogger(__name__)

client = get_absortium_client(api_key=settings.ABSORTIUM_API_KEY,
                              api_secret=settings.ABSORTIUM_API_SECRET,
                              base_api_uri=constants.BACKEND_URL)

storage = {
    'orders': {
        'sell': [],
        'buy': []
    }
}


def cancel_orders():
    for order in [order for order in client.orders.list() if order['status'] not in ['canceled', 'completed']]:
        client.orders.cancel(pk=order['pk'])


def signal_handler(*args, **kwargs):
    print('You pressed Ctrl+C! Please wait for orders canceling...')
    cancel_orders()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


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
        cancel_orders()

        # 1. Turn on Poloniex orders update.
        self.push.subscribe(topic=constants.CURRENCY_PAIR, handler=PoloniexApp.updates_handler)

        # 2. Get Poloniex orders.
        orders = await self.public.returnOrderBook(currencyPair=constants.CURRENCY_PAIR, depth=constants.COUNT)

        # 3. Merge Poloniex orders.
        synchronize_orders(storage, orders)

        while True:
            for order_type in ['sell', 'buy']:
                from_currency = get_from_currency(order_type, constants.CURRENCY_PAIR)

                # 1. Get Absortium orders.
                absortium_orders = client.orders.list(order_type=order_type)

                # 2. Crate orders on Poloniex.
                create_poloniex_orders(absortium_orders)

                # 3. Leave only 'init' and 'pending' orders.
                absortium_orders = filter_orders(absortium_orders)

                # 4. Calculate how many amount we have to operate with.
                account = client.accounts.retrieve(currency=from_currency)
                accounts_balance = D(account['amount'])
                amount = get_locked_balance(absortium_orders) + accounts_balance

                # 5. Get Poloniex orders and cut off redundant.
                poloniex_orders = storage['orders'][order_type]
                poloniex_orders = cut_off_orders(amount, poloniex_orders)

                # 6. What should have to do to sync the orders?
                actions = create_actions(absortium_orders, poloniex_orders)
                apply_action(client, actions)

            await asyncio.sleep(1)
