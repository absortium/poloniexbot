__author__ = 'andrew.shvv@gmail.com'

from decimal import Decimal

MAX_DIGITS = 19
DECIMAL_PLACES = 12

OFFER_MAX_DIGITS = MAX_DIGITS + (MAX_DIGITS - DECIMAL_PLACES)
ACCOUNT_MAX_DIGITS = OFFER_MAX_DIGITS

AMOUNT_MIN_VALUE = Decimal(1 / 10 ** DECIMAL_PLACES)
PRICE_MIN_VALUE = Decimal(1 / 10 ** DECIMAL_PLACES)

POLONIEX_ORDER_MODIFIED = "orderBookModify"
POLONIEX_ORDER_REMOVED = "orderBookRemove"