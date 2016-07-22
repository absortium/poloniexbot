from decimal import Decimal as D

from django.db import IntegrityError

from absortium.error import LockFailureError, NotEnoughMoneyError
from absortium.error import ValidationError
from poloniexbot import constants
from poloniexbot.celery import tasks
from poloniexbot.models import Redirect

__author__ = 'andrew.shvv@gmail.com'


def filter_orders(orders):
    return [order for order in orders
            if order['status'] in ['init', 'pending']]


def get_locked_balance(orders):
    """
        Calculate amount of money that are locked in orders.
    """
    return sum([D(order['amount']) for order in orders
                if order['status'] in ['init', 'pending']])


def create_actions(absortium_orders, poloniex_orders):
    """
        Create actions that are needed for sync the Absortium and Poloniex order tables.
    """

    def update(old_order, new_orders):
        for k, v in new_orders.items():
            old_order[k] = v
        return old_order

    absortium_orders = {order['price']: order for order in absortium_orders}
    poloniex_orders = {order['price']: order for order in poloniex_orders}

    absortium_prices = absortium_orders.keys()
    poloniex_prices = poloniex_orders.keys()

    delete_orders = list(set(absortium_prices) - set(poloniex_prices))
    create_orders = list(set(poloniex_prices) - set(absortium_prices))
    update_orders = list(set(poloniex_prices) & set(absortium_prices))

    actions = []

    for price in delete_orders:
        actions.append((constants.PRIORITY_DELETE, constants.ACTION_DELETE, absortium_orders[price]))

    for price in create_orders:
        actions.append((constants.PRIORITY_CREATE, constants.ACTION_CREATE, poloniex_orders[price]))

    for price in update_orders:
        difference = D(poloniex_orders[price]['amount']) - D(absortium_orders[price]['amount'])

        if difference > 0:
            actions.append((constants.PRIORITY_INCREASE,
                            constants.ACTION_INCREASE,
                            update(absortium_orders[price], poloniex_orders[price])))
        elif difference < 0:
            actions.append((constants.PRIORITY_DECREASE,
                            constants.ACTION_DECREASE,
                            update(absortium_orders[price], poloniex_orders[price])))

    def key(elem):
        price = D(elem[2]['price'])
        priority = elem[0]
        return priority, price

    actions = sorted(actions, key=key)

    return actions


def cut_off_orders(balance, poloniex_orders):
    """
       Leaving only those Poloniex orders which we can afford.
    """
    new_orders = []

    if balance != 0:
        for order in poloniex_orders:
            amount = D(order['amount'])

            if amount > D("0.001"):
                if balance > amount:
                    new_orders.append(order)
                    balance -= amount
                else:
                    order['amount'] = str(balance)
                    new_orders.append(order)
                    break

    return new_orders


def convert(order):
    """
        Convert Poloniex order notification to Absortium order data.
    """

    price = str(order["rate"])
    amount = str(order.get("amount", 0))

    if order["type"] in ["bid", "bids"]:
        order_type = "buy"
    elif order["type"] in ["ask", "asks"]:
        order_type = "sell"
    else:
        raise Exception("Unknown order type")

    return {
        "pair": order["pair"].lower(),
        "order_type": order_type,
        "price": price,
        "amount": amount,
        "need_approve": True
    }


def update_storage(storage, new_order):
    def get_index(price, orders):
        for index, order in enumerate(orders):
            if D(order['price']) == D(price):
                return index

        raise IndexError

    orders = storage['orders'][new_order['order_type']]
    is_zero_amount = D(new_order['amount']) == D("0")

    try:
        index = get_index(new_order['price'], orders)

        if is_zero_amount:
            del orders[index]
        else:
            orders[index] = new_order

    except IndexError:
        if not is_zero_amount:
            orders.append(new_order)

    storage['orders'][new_order['order_type']] = sorted(orders, key=lambda order: D(order['price']))[:20]


def synchronize_orders(storage, orders):
    def sync(orders, order_book_type):
        for price, amount in orders[order_book_type]:
            order = {
                "rate": price,
                "amount": amount,
                "pair": constants.CURRENCY_PAIR,
                "type": order_book_type
            }

            order = convert(order)
            update_storage(storage, order)

    sync(orders, "bids")
    sync(orders, "asks")


def apply_action(client, actions):
    for elem in actions:
        try:
            """
                To be sure that while updating the order it status is not changed from 'pending' or 'init'
                to 'approving' (someone accept the order) we firstly need to lock it. Because we do not want to
                'cancel' order which was accepted by some user. And also we do not want update order that was
                changed because it may lead to strange behaviour.
            """

            action = elem[1]
            order = elem[2]

            if action == constants.ACTION_DELETE:
                client.orders.lock(**order)
                client.orders.cancel(**order)

            elif action in [constants.ACTION_DECREASE, constants.ACTION_INCREASE]:
                del order['total']
                client.orders.lock(**order)
                client.orders.update(**order)
                client.orders.unlock(**order)

            elif action == constants.ACTION_CREATE:
                client.orders.create(**order)

        except LockFailureError:
            pass
        except ValidationError:
            if action in [constants.ACTION_DECREASE, constants.ACTION_INCREASE]:
                client.orders.unlock(**order)
            pass
        except NotEnoughMoneyError:
            if action in [constants.ACTION_DECREASE, constants.ACTION_INCREASE]:
                client.orders.unlock(**order)
            return


def get_from_currency(order_type, pair):
    if order_type == "sell":
        return pair.split('_')[1]
    else:
        return pair.split('_')[0]


def get_to_currency(order_type, pair):
    if order_type == "sell":
        return pair.split('_')[1]
    else:
        return pair.split('_')[0]


def create_poloniex_orders(absortium_orders):
    orders = [order for order in absortium_orders if order['status'] == 'approving']

    for order in orders:
        try:
            redirect = Redirect(absortium_order_pk=order['pk'])
            redirect.save()
            tasks.process_redirect(redirect_pk=redirect.pk)
        except IntegrityError:
            """
                Redirect was somehow created before or simultaneously in another thread.
            """
        pass
