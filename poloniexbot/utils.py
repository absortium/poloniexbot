from decimal import Decimal as D

from poloniexbot import constants

__author__ = 'andrew.shvv@gmail.com'


def filter_orders(orders):
    return [order for order in orders
            if order['status'] in ['init', 'pending']]


def get_locked_balance(orders):
    return sum([D(order['amount']) for order in orders
                if order['status'] in ['init', 'pending']])


def create_actions(absortium_orders, poloniex_orders):
    def update(old_order, new_orders):
        for k, v in new_orders.items():
            old_order[k] = v
        return old_order

    absortium_orders = {order['price']: order for order in absortium_orders}
    poloniex_orders = {order['price']: order for order in poloniex_orders}

    actions = {
        'update': [],
        'delete': [],
        'create': []
    }

    absortium_prices = absortium_orders.keys()
    poloniex_prices = poloniex_orders.keys()

    # 1. Check that absortium
    delete_orders = list(set(absortium_prices) - set(poloniex_prices))
    create_orders = list(set(poloniex_prices) - set(absortium_prices))
    update_orders = list(set(poloniex_prices) & set(absortium_prices))

    for price in delete_orders:
        actions['delete'].append(absortium_orders[price])

    for price in create_orders:
        actions['create'].append(poloniex_orders[price])

    for price in update_orders:
        if D(absortium_orders[price]['amount']) != D(poloniex_orders[price]['amount']):
            actions['update'].append(update(absortium_orders[price], poloniex_orders[price]))

    return actions


def cut_off_orders(balance, orders):
    new_orders = []

    for order in orders:
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
