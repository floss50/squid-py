from web3 import HTTPProvider, Web3

from squid_py.config_provider import ConfigProvider


class Web3Provider(object):
    """Provides the Web3 instance."""
    _web3 = None

    @staticmethod
    def get_web3():
        """Return the web3 instance to interact with the ethereum client."""
        if Web3Provider._web3 is None:
            config = ConfigProvider.get_config()
            provider = config.web3_provider if config.web3_provider else HTTPProvider(
                config.keeper_url)
            Web3Provider._web3 = Web3(provider)
            # Reset attributes to avoid lint issue about no attribute
            Web3Provider._web3.eth = getattr(Web3Provider._web3, 'eth')
            Web3Provider._web3.net = getattr(Web3Provider._web3, 'net')
            Web3Provider._web3.personal = getattr(Web3Provider._web3, 'personal')
            Web3Provider._web3.version = getattr(Web3Provider._web3, 'version')
            Web3Provider._web3.txpool = getattr(Web3Provider._web3, 'txpool')
            Web3Provider._web3.miner = getattr(Web3Provider._web3, 'miner')
            Web3Provider._web3.admin = getattr(Web3Provider._web3, 'admin')
            Web3Provider._web3.parity = getattr(Web3Provider._web3, 'parity')
            Web3Provider._web3.testing = getattr(Web3Provider._web3, 'testing')

        return Web3Provider._web3
