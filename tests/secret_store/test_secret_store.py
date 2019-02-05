import hashlib
import json
import secrets

from squid_py import ConfigProvider
from squid_py.secret_store.secret_store import SecretStore
from squid_py.secret_store.secret_store_provider import SecretStoreProvider
from tests.resources.helper_functions import get_resource_path
from tests.resources.tiers import e2e_test


@e2e_test
def test_secret_store():
    test_document = get_resource_path('ddo', 'ddo_sample1.json')
    with open(test_document, 'r') as file_handle:
        metadata = json.load(file_handle)
    metadata_json = json.dumps(metadata)
    document_id = hashlib.sha256((metadata_json + secrets.token_hex(32)).encode()).hexdigest()
    print(document_id)
    config = ConfigProvider.get_config()
    args = SecretStoreProvider.get_args_from_config(config)
    result = SecretStore(*args).encrypt_document(document_id, metadata_json)
    print(result)
    assert json.loads(SecretStore(*args).decrypt_document(document_id, result)) == metadata
