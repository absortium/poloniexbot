__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase, APIClient

from core.utils.logging import getLogger

logger = getLogger(__name__)


class PoloniexBotTestMixin():
    def get_first(self, response):
        self.assertEqual(response.status_code, HTTP_200_OK)

        json = response.json()
        results = json['results']

        self.assertGreaterEqual(len(results), 0)

        return results[0]

    def interrupt(self):
        input("To continue press some button:")


@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True)
class PoloniexBotUnitTest(APITestCase,
                          PoloniexBotTestMixin):
    def setUp(self):
        super().setUp()

        User = get_user_model()
        user = User(username="primary")
        user.save()

        self.user = user
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def tearDown(self):
        super().tearDown()
