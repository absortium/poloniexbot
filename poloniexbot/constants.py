__author__ = "andrew.shvv@gmail.com"

from decimal import Decimal

MAX_DIGITS = 19
DECIMAL_PLACES = 12

OFFER_MAX_DIGITS = MAX_DIGITS + (MAX_DIGITS - DECIMAL_PLACES)
ACCOUNT_MAX_DIGITS = OFFER_MAX_DIGITS

AMOUNT_MIN_VALUE = Decimal(1 / 10 ** DECIMAL_PLACES)
PRICE_MIN_VALUE = Decimal(1 / 10 ** DECIMAL_PLACES)

POLONIEX_ORDER_MODIFIED = "orderBookModify"
POLONIEX_ORDER_REMOVED = "orderBookRemove"

CURRENCY_PAIR = "BTC_ETH"
COUNT = 20

BACKEND_URL = "http://docker.backend:3000"

CELERY_MAX_RETRIES = 20
RETRY_COUNTDOWN = 10

# lower number - higher priority
PRIORITY_DELETE = 0
PRIORITY_DECREASE = 0
PRIORITY_INCREASE = 1
PRIORITY_CREATE = 1

ACTION_DELETE = "delete"
ACTION_DECREASE = "decrease"
ACTION_INCREASE = "increase"
ACTION_CREATE = "create"

REDIRECT_INIT = "init"
REDIRECT_PENDING = "pending"
REDIRECT_CANCELED = "canceled"
REDIRECT_COMPLETED = "completed"
REDIRECT_APPROVING = "approving"
REDIRECT_TRANSMISSION = "transmission"
REDIRECT_ABANDONED = "abandoned"

AVAILABLE_REDIRECT_STATUSES = [
    REDIRECT_INIT,
    REDIRECT_PENDING,
    REDIRECT_CANCELED,
    REDIRECT_COMPLETED,
    REDIRECT_ABANDONED,
    REDIRECT_TRANSMISSION,
    REDIRECT_APPROVING
]

BTC = "btc"
ETH = "eth"
AVAILABLE_CURRENCIES = [
    BTC,
    ETH
]

SYSTEM_ABSORTIUM = "absortium"
SYSTEM_POLONIEX = "poloniex"

AVAILABLE_SYSTEMS = [
    SYSTEM_ABSORTIUM,
    SYSTEM_POLONIEX
]
