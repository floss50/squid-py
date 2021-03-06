"""Keeper module to call keeper-contracts."""

from squid_py.keeper.contract_base import ContractBase
from squid_py.keeper.web3_provider import Web3Provider


class Token(ContractBase):
    """Class representing the Token contract."""
    CONTRACT_NAME = 'OceanToken'

    def get_token_balance(self, account_address):
        """
        Retrieve the amount of tokens of an account address.

        :param account_address: Account address, str
        :return: int
        """
        return self.contract_concise.balanceOf(account_address)

    def get_allowance(self, owner_address, spender_address):
        """

        :param owner_address: Address, str
        :param spender_address: Address, str
        :return:
        """
        return self.contract_concise.allowance(owner_address, spender_address)

    def token_approve(self, spender_address, price, from_account):
        """
        Approve the passed address to spend the specified amount of tokens.

        :param spender_address: Account address, str
        :param price: Price, int
        :param from_account: Account address, str
        :return:
        """
        if not Web3Provider.get_web3().isChecksumAddress(spender_address):
            spender_address = Web3Provider.get_web3().toChecksumAddress(spender_address)

        from_account.unlock()
        tx_hash = self.contract_concise.approve(
            spender_address,
            price,
            transact={'from': from_account.address}
        )
        return self.get_tx_receipt(tx_hash).status == 1

    def transfer(self, receiver_address, amount, from_account):
        """
        Transfer tokens from one account to the receiver address.

        :param receiver_address: Address of the transfer receiver, str
        :param amount: Amount of tokens, int
        :param from_account: Sender account, Account
        :return: bool
        """
        tx_hash = self.contract_concise.transfer(
            receiver_address,
            amount,
            transact={'from': from_account.address}
        )
        return self.get_tx_receipt(tx_hash).status == 1

    def total_supply(self):
        """

        :return:
        """
        return self.contract_concise.totalSupply()

    def increase_allowance(self, spender_address, added_value, owner_account):
        """

        :param spender_address:
        :param added_value:
        :param owner_account:
        :return:
        """
        tx_hash = self.contract_concise.increaseAllowance(
            spender_address,
            added_value,
            transact={'from': owner_account.address}
        )
        return self.get_tx_receipt(tx_hash).status == 1

    def decrease_allowance(self, spender_address, subtracted_value, owner_account):
        """

        :param spender_address:
        :param subtracted_value:
        :param owner_account:
        :return:
        """
        tx_hash = self.contract_concise.decreaseAllowance(
            spender_address,
            subtracted_value,
            transact={'from': owner_account.address}
        )
        return self.get_tx_receipt(tx_hash).status == 1
