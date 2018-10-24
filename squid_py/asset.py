import os
import logging
import json
from .ddo import DDO
import pathlib

class Asset:
    def __init__(self, asset_id=None, publisher_id=None, price=None, ddo=None):
        """
        Represent an asset in the MetaData store

        Constructor methods:
            1. Direct instantiation Asset(**kwargs)
                - Use this method to manually build an asset
            2. From a json DDO file Asset.from_ddo_json_file()
                - Create an asset based on a DDO file
            3.

        :param asset_id: The same as the DID
        :param publisher_id:
        :param price:
        :param ddo: DDO instance
        """

        self.asset_id = asset_id
        self.publisher_id = publisher_id
        self.price = price
        self.ddo = ddo

    @classmethod
    def from_ddo_json_file(cls,json_file_path):
        this_asset = cls()
        this_asset.ddo = DDO.from_json_file(json_file_path)
        this_asset.asset_id = this_asset.ddo['id']
        logging.debug("Asset {} created from ddo file {} ".format(this_asset.asset_id, json_file_path))
        return this_asset

    def purchase(self, consumer, timeout):
        """
        Generate an order for purchase of this Asset

        :param timeout:
        :param consumer: Account object of the requester
        :return: Order object
        """
        # Check if asset exists

        # Approve the token transfer

        # Submit access request

        return

    def consume(self, order, consumer):
        """

        :param order: Order object
        :param consumer: Consumer Account
        :return: access_url
        :rtype: string
        :raises :
        """

        # Get access token (jwt)

        # Download the asset from the provider using the URL in access token
        # Decode the the access token, get service_endpoint and request_id

        return

    def get_DDO(self):
        """

        :return:
        """

    def get_DID(self):
        pass

    def publish_metadata(self):
        pass

    def get_metadata(self):
        pass

    def update_metadata(self):
        pass

    def retire_metadata(self):
        pass

    def get_service_agreements(self):
        pass

    def __str__(self):
        return "Asset {} for {}, published by {}".format(self.asset_id, self.price,self.publisher_id)



