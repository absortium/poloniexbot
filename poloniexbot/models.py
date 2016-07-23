from django.db import models

from core.utils.logging import getPrettyLogger
from core.utils.model import calculate_len
from poloniexbot import constants

logger = getPrettyLogger(__name__)

__author__ = 'andrew.shvv@gmail.com'


class Redirect(models.Model):
    status = models.CharField(max_length=calculate_len(constants.AVAILABLE_REDIRECT_STATUSES),
                              default=constants.REDIRECT_INIT)

    poloniex_order_pk = models.IntegerField()
    absortium_order_pk = models.IntegerField()

    celery_task_id = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def lock(**kwargs):
        return Redirect.objects.select_for_update().get(**kwargs)

class Transmission(models.Model):
    currency = models.CharField(max_length=calculate_len(constants.AVAILABLE_CURRENCIES))

    address = models.CharField(max_length=50)

    system = models.CharField(max_length=calculate_len(constants.AVAILABLE_SYSTEMS))

    created = models.DateTimeField(auto_now_add=True)

    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES,
                                 default=0)

    redirect = models.ForeignKey(Redirect, related_name="transmission")
