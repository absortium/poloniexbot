import os

import requests

from absortium.auth import HMACAuth
from absortium.compat import imap, urljoin, quote
from absortium.services import Account, Withdrawal, Order
from absortium.util import encode_params

ABSORTIUM_CRT_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'ca-absortium.crt')

ABSORTIUM_CALLBACK_PUBLIC_KEY_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'absortium-callback.pub')

__author__ = 'andrew.shvv@gmail.com'


class Client():
    """ API Client for the Absortium API.

    Entry point for making requests to the Absortium API. Provides helper methods
    for common API endpoints, as well as niceties around response verification
    and formatting.

    Any errors will be raised as exceptions. These exceptions will always be
    subclasses of `absortium.error.APIError`. HTTP-related errors will also be
    subclasses of `requests.HTTPError`.
    """
    VERIFY_SSL = False
    API_VERSION = '2016-07-17'

    cached_callback_public_key = None

    def __init__(self, api_key, api_secret, base_api_uri, api_version=None):
        if not api_key:
            raise ValueError('Missing `api_key`.')
        if not api_secret:
            raise ValueError('Missing `api_secret`.')

        # Allow passing in a different API base.
        self.BASE_API_URI = base_api_uri

        self.API_VERSION = api_version or self.API_VERSION

        # Set up a requests session for interacting with the API.
        self.session = self._build_session(HMACAuth, api_key, api_secret, self.API_VERSION)

        self.order = Order(self)
        self.withdrawal = Withdrawal(self)
        self.account = Account(self)

    def _build_session(self, auth_class, *args, **kwargs):
        """Internal helper for creating a requests `session` with the correct
        authentication handling."""
        session = requests.session()
        session.auth = auth_class(*args, **kwargs)
        session.headers.update({'Accept': 'application/json',
                                'Content-Type': 'application/json',
                                'User-Agent': 'absortium/python/3.0'})
        return session

    def _create_api_uri(self, *parts):
        """Internal helper for creating fully qualified endpoint URIs."""
        parts += ('/',)
        return urljoin(self.BASE_API_URI, '/'.join(imap(quote, parts)))

    def _request(self, method, *relative_path_parts, **kwargs):
        """Internal helper for creating HTTP requests to the ethwallet API.

        Raises an APIError if the response is not 20X. Otherwise, returns the
        response object. Not intended for direct use by API consumers.
        """
        uri = self._create_api_uri(*relative_path_parts)
        data = kwargs.get('data', None)
        if data and isinstance(data, dict):
            kwargs['data'] = encode_params(data)
        if self.VERIFY_SSL:
            kwargs.setdefault('verify', ABSORTIUM_CRT_PATH)
        else:
            kwargs.setdefault('verify', False)
        kwargs.update(verify=self.VERIFY_SSL)
        response = getattr(self.session, method)(uri, **kwargs)
        return self._handle_response(response)

    def _handle_response(self, response):
        return response.json()

    def get(self, *args, **kwargs):
        return self._request('get', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._request('post', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._request('put', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._request('delete', *args, **kwargs)
