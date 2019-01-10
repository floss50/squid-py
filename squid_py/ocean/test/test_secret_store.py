import hashlib
import json
import os
import secrets

from secret_store_client.client import Client

from squid_py.config import Config
from squid_py.test_resources.helper_functions import get_resource_path
from ...test_resources.tiers import e2e_test

secret_store_url = 'http://localhost:8010'
parity_client_publish_url = 'http://localhost:9545'
publisher_address = "0x594d9f933f4f2df6bb66bb34e7ff9d27acc1c019"
publisher_password = 'password'


@e2e_test
def test_secret_store():
    config = Config('config_local.ini')
    test_document = get_resource_path('metadata', 'sample_metadata1.json')
    with open(test_document, 'r') as file_handle:
        metadata = json.load(file_handle)

    publisher = Client(config.secret_store_url, config.parity_url,
                       config.parity_address, config.parity_password)

    metadata_json = json.dumps(metadata)
    document_id = hashlib.sha256((metadata_json + secrets.token_hex(32)).encode()).hexdigest()
    print(document_id)
    result = publisher.publish_document(document_id, metadata_json)
    print(result)
    assert json.loads(publisher.decrypt_document(document_id, result)) == metadata
