import hashlib
import json
import secrets
from unittest.mock import Mock, MagicMock

from squid_py import ConfigProvider, Account
from squid_py.secret_store.secret_store import SecretStore
from tests.resources.helper_functions import get_resource_path
from tests.resources.tiers import e2e_test


@e2e_test
def test_secret_store_encrypt_decrypt():
    test_document = get_resource_path('ddo', 'ddo_sample1.json')
    with open(test_document, 'r') as file_handle:
        metadata = json.load(file_handle)
    metadata_json = json.dumps(metadata)
    document_id = hashlib.sha256((metadata_json + secrets.token_hex(32)).encode()).hexdigest()
    print(document_id)
    config = ConfigProvider.get_config()
    ss_client = Mock
    ss_client.publish_document = MagicMock(return_value='!!document!!')
    ss_client.decrypt_document = MagicMock(return_value=metadata_json)
    SecretStore.set_client(ss_client)

    ss_args = (config.secret_store_url, config.parity_url, Account('0x0000', 'aaa'))
    result = SecretStore(*ss_args).encrypt_document(document_id, metadata_json)
    print(result)
    assert SecretStore(*ss_args).decrypt_document(document_id, result) == metadata_json


def test_set_secret_store_url():
    pass


def test_set_client():
    pass
