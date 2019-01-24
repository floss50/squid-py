"""
    Keeper Contract Base

    All keeper contract inherit from this base class
"""

import logging

from squid_py.keeper.web3_provider import Web3Provider

logger = logging.getLogger('keeper')


class ContractBase(object):
    """Base class for all contract objects."""

    def __init__(self, contract_name, contract_handler=None):

        self.name = contract_name

        if not contract_handler:
            from squid_py.keeper.contract_handler import ContractHandler
            contract_handler = ContractHandler
        self.contract_concise = contract_handler.get_concise_contract(contract_name)
        self.contract = contract_handler.get(contract_name)

        logger.debug(f'Loaded {self}')

    @property
    def _contract_concise(self):
        return self.contract_concise

    @property
    def _contract(self):
        return self.contract

    @property
    def address(self):
        """Return the ethereum address of the solidity contract deployed
        in current keeper network.
        """
        return self._contract.address

    @property
    def events(self):
        """Expose the underlying contract's events.

        :return:
        """
        return self.contract.events

    def to_checksum_address(self, address):
        """
        Validate the address provided.

        :param address:
        :return:
        """
        return Web3Provider.get_web3().toChecksumAddress(address)

    def get_tx_receipt(self, tx_hash):
        """
        Get the receipt of a tx.

        :param tx_hash:
        :return:
        """
        Web3Provider.get_web3().eth.waitForTransactionReceipt(tx_hash)
        return Web3Provider.get_web3().eth.getTransactionReceipt(tx_hash)

    def __str__(self):
        return f'{self.name} at {self.address}'
