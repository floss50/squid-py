from squid_py.keeper.contract_base import ContractBase


class AccessConditions(ContractBase):

    def __init__(self, web3, contract_path):
        super().__init__(web3, contract_path, 'AccessConditions')
