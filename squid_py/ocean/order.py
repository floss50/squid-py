"""Ocean module."""

from .ocean_base import OceanBase


class Order(OceanBase):

    def __init__(self, order_id, asset, timeout, pub_key, key, paid, status):
        self.order_id = order_id
        self.asset = asset
        self.asset_id = self.asset.id
        self.timeout = timeout
        self.pub_key = pub_key
        self.key = key
        self.paid = paid
        self.status = status
        OceanBase.__init__(self, self.order_id)

    def get_status(self):
        return 0

    def verify_payment(self):
        return False

    def pay(self):
        return ''

    def commit(self):
        return False

    def consume(self):
        return ''
