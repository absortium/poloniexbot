from absortium import constants

__author__ = 'andrew.shvv@gmail.com'


class Base():
    def __init__(self, client):
        self.client = client


class Withdrawal(Base):
    def list(self, currency=None):
        params = {
            'currency': currency
        }

        return self.client.get('api', 'withdrawals', data=params)

    def create(self, amount, address):
        data = {
            'amount': amount,
            'address': address
        }

        return self.client.post('api', 'withdrawals', data=data)


class Deposit(Base):
    def list(self, currency=None):
        params = {
            'currency': currency
        }

        return self.client.get('api', 'deposits', data=params)


class Order(Base):
    def create(self,
               price,
               amount=None,
               total=None,
               order_type=None,
               pair=constants.PAIR_BTC_ETH,
               need_approve=False):
        data = {
            'type': order_type,
            'price': price,
            'pair': pair,
            'total': total,
            'amount': amount,
            'need_approve': need_approve
        }

        return self.client.post('api', 'orders', data=data)

    def retrieve(self, pk):
        return self.client.get('api', 'orders', pk)

    def list(self,
             order_type=None,
             pair=None):
        params = {
            'type': order_type,
            'pair': pair,
        }
        return self.client.get('api', 'orders', data=params)

    def update(self,
               pk,
               price,
               amount=None,
               total=None):
        data = {
            'price': price,
            'amount': amount,
            'total': total,
        }
        return self.client.put('api', 'orders', pk, data=data)

    def cancel(self, pk):
        return self.client.delete('api', 'orders', pk)

    def approve(self, pk):
        return self.client.delete('api', 'orders', pk, 'approve')


class Account(Base):
    def list(self):
        return self.client.get('api', 'accounts')

    def retrieve(self, pk):
        return self.client.post('api', 'accounts', pk)

    def create(self, currency):
        data = {'currency': currency}
        return self.client.post('api', 'accounts', data=data)
