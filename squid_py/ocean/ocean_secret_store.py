"""Ocean module."""
import logging

from squid_py.accounts.account import Account
from squid_py.secret_store.secret_store_provider import SecretStoreProvider

logger = logging.getLogger(__name__)


class OceanSecretStore:
    def __init__(self, config):
        self._config = config
        if config.secret_store_url and config.parity_url and config.parity_address:
            logger.info(f'\tSecretStore: url {config.secret_store_url}, '
                        f'parity-client {config.parity_url}, '
                        f'account {config.parity_address}')

        self._secret_store_url = config.secret_store_url
        self._parity_url = config.parity_url
        self._account = Account(config.parity_address, config.parity_password)

    def _secret_store(self, account):
        return SecretStoreProvider.get_secret_store(
            self._secret_store_url,
            self._parity_url,
            account or self._account
        )

    def encrypt(self, document_id, content, account):
        """

        :param document_id: hex str id of document to use for encryption session
        :param content: str to be encrypted
        :param account: Account instance encrypting this content
        :return: hex str encrypted content
        """
        return self._secret_store(account).encrypt_document(document_id, content)

    def decrypt(self, document_id, encrypted_content, account):
        """

        :param document_id: hex str id of document to use to retrieve the decryption keys
        :param encrypted_content: hex str
        :param account: Account instance to use for decrypting the `encrypted_content`
        :return: str original content
        """
        return self._secret_store(account).decrypt_document(document_id, encrypted_content)
