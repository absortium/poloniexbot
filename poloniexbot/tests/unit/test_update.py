from decimal import Decimal as D

from core.utils.logging import getPrettyLogger
from poloniexbot import constants
from poloniexbot.tests.base import PoloniexBotUnitTest
from poloniexbot.utils import cut_off_orders, create_actions

__author__ = 'andrew.shvv@gmail.com'

logger = getPrettyLogger(__name__)


class UpdateTest(PoloniexBotUnitTest):
    def init_check(self, actions):
        def check(action=None, pk=None, price=None):

            for elem in actions:
                elem_action = elem[1]
                elem_order = elem[2]

                c1 = elem_order['pk'] == pk if pk else True
                c2 = D(elem_order['price']) == D(price) if price else True
                c3 = elem_action == action if action else True

                if c1 and c2 and c3:
                    return True

            return False

        return check

    def test_cut_off_orders(self):
        balance = 10
        poloniex_orders = [
            {'amount': '1', 'price': '1'},
            {'amount': '8', 'price': '2'},
            {'amount': '10', 'price': '3'}
        ]

        orders = cut_off_orders(balance, poloniex_orders)
        self.assertEqual(len(orders), 3)
        self.assertEqual(D(orders[0]['amount']), 1)
        self.assertEqual(D(orders[1]['amount']), 8)
        self.assertEqual(D(orders[2]['amount']), 1)

    def test_cut_off_orders_zero(self):
        balance = 10
        poloniex_orders = [
            {'amount': '1', 'price': '1'},
            {'amount': '9', 'price': '2'}
        ]

        orders = cut_off_orders(balance, poloniex_orders)
        self.assertEqual(len(orders), 2)
        self.assertEqual(D(orders[0]['amount']), 1)
        self.assertEqual(D(orders[1]['amount']), 9)

    def test_cut_off_zero_balance(self):
        balance = 0
        poloniex_orders = [
            {'amount': '1', 'price': '0.01670620'}
        ]

        orders = cut_off_orders(balance, poloniex_orders)
        self.assertEqual(len(orders), 0)

    def test_cut_off_orders_long(self):
        balance = 10
        poloniex_orders = [
            {'amount': '1', 'price': '1'},
            {'amount': '8', 'price': '2'},
            {'amount': '1', 'price': '3'},
            {'amount': '9', 'price': '4'}
        ]

        orders = cut_off_orders(balance, poloniex_orders)
        self.assertEqual(len(orders), 3)
        self.assertEqual(D(orders[0]['amount']), 1)
        self.assertEqual(D(orders[1]['amount']), 8)
        self.assertEqual(D(orders[2]['amount']), 1)

    def test_action_without_update(self):
        poloniex_orders = [
            {'price': '1', 'amount': '1'}
        ]

        absortium_orders = [
            {'pk': 1, 'price': '1', 'amount': '1'}
        ]

        actions = create_actions(absortium_orders, poloniex_orders)
        check = self.init_check(actions)
        self.assertEqual(check(pk=1), False)

    def test_action_with_update(self):
        poloniex_orders = [
            {'price': '1', 'amount': '2'}
        ]

        absortium_orders = [
            {'pk': 1, 'price': '1', 'amount': '1'}
        ]

        actions = create_actions(absortium_orders, poloniex_orders)
        check_that = self.init_check(actions)

        self.assertEqual(check_that(price='1', action=constants.ACTION_INCREASE), True)

    def test_action_create(self):
        poloniex_orders = [
            {'price': '2', 'amount': '1'}
        ]
        absortium_orders = []

        actions = create_actions(absortium_orders, poloniex_orders)
        check_that = self.init_check(actions)

        self.assertEqual(check_that(price='2', action=constants.ACTION_CREATE), True)

    def test_action_decrease(self):
        poloniex_orders = [
            {'amount': '8', 'price': '1'},
            {'amount': '2', 'price': '2'},
        ]

        absortium_orders = [
            {'pk': 1, 'amount': '10', 'price': '1'},
        ]

        actions = create_actions(absortium_orders, poloniex_orders)
        check_that = self.init_check(actions)

        self.assertEqual(check_that(price='1', action=constants.ACTION_DECREASE), True)
        self.assertEqual(check_that(price='2', action=constants.ACTION_CREATE), True)

    def test_action_delete(self):
        poloniex_orders = []
        absortium_orders = [
            {'pk': 1, 'price': '2', 'amount': 1}
        ]

        actions = create_actions(absortium_orders, poloniex_orders)
        check_that = self.init_check(actions)

        self.assertEqual(check_that(pk=1, action=constants.ACTION_DELETE), True)
