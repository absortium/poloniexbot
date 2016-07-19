from decimal import Decimal as D

from core.utils.logging import getPrettyLogger
from poloniexbot.tests.base import PoloniexBotUnitTest
from poloniexbot.utils import cut_off_orders, create_actions

__author__ = 'andrew.shvv@gmail.com'

logger = getPrettyLogger(__name__)


class UpdateTest(PoloniexBotUnitTest):
    def init_check(self, actions):
        def check(action, pk=None, price=None):
            if pk:
                return pk in [order['pk'] for order in actions[action]]
            elif price:
                return price in [order['price'] for order in actions[action]]

        return check

    def test_cut_off_orders(self):
        balance = 10
        poloniex_orders = [
            {
                'amount': '1',
                'price': '0.01670620',
            },
            {
                'amount': '8',
                'price': '0.01671164',
            },
            {
                'amount': '10',
                'price': '0.01671265',
            }
        ]

        orders = cut_off_orders(balance, poloniex_orders)
        self.assertEqual(len(orders), 3)
        self.assertEqual(D(orders[0]['amount']), 1)
        self.assertEqual(D(orders[1]['amount']), 8)
        self.assertEqual(D(orders[2]['amount']), 1)

    def test_cut_off_orders_zero(self):
        balance = 10
        poloniex_orders = [
            {
                'amount': '1',
                'price': '0.01670620',
            },
            {
                'amount': '9',
                'price': '0.01671164',
            }
        ]

        orders = cut_off_orders(balance, poloniex_orders)
        self.assertEqual(len(orders), 2)
        self.assertEqual(D(orders[0]['amount']), 1)
        self.assertEqual(D(orders[1]['amount']), 9)

    def test_cut_off_orders_long(self):
        balance = 10
        poloniex_orders = [
            {
                'amount': '1',
                'price': '0.01670620',
            },
            {
                'amount': '8',
                'price': '0.01671164',
            },
            {
                'amount': '1',
                'price': '0.01671164',
            },
            {
                'amount': '9',
                'price': '0.01671164',
            }
        ]

        orders = cut_off_orders(balance, poloniex_orders)
        self.assertEqual(len(orders), 3)
        self.assertEqual(D(orders[0]['amount']), 1)
        self.assertEqual(D(orders[1]['amount']), 8)
        self.assertEqual(D(orders[2]['amount']), 1)

    def test_action_without_update(self):
        poloniex_orders = [{'price': '1', 'amount': 1}]
        absortium_orders = [{'pk': 1, 'price': '1', 'amount': '1'}]

        actions = create_actions(absortium_orders, poloniex_orders)
        check = self.init_check(actions)
        self.assertEqual(check(pk=1, action='update'), False)

    def test_action_with_update(self):
        poloniex_orders = [{'price': '1', 'amount': 2}]
        absortium_orders = [{'pk': 1, 'price': '1', 'amount': '1'}]

        actions = create_actions(absortium_orders, poloniex_orders)
        check_that = self.init_check(actions)

        self.assertEqual(check_that(pk=1, action='update'), True)

    def test_action_create(self):
        poloniex_orders = [{'price': '2', 'amount': 1}]
        absortium_orders = []

        actions = create_actions(absortium_orders, poloniex_orders)
        check_that = self.init_check(actions)

        self.assertEqual(check_that(price='2', action='create'), True)

    def test_action_delete(self):
        poloniex_orders = []
        absortium_orders = [{'pk': 1, 'price': '2', 'amount': 1}]

        actions = create_actions(absortium_orders, poloniex_orders)
        check_that = self.init_check(actions)

        self.assertEqual(check_that(pk=1, action='delete'), True)
