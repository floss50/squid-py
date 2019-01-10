"""
    Test did_lib
"""
import secrets

import pytest
from web3 import Web3

from squid_py.did import (
    did_parse,
    is_did_valid,
    id_to_did,
    did_to_id,
    did_to_id_bytes,
    DID,
    OCEAN_PREFIX
)
from ..test_resources.tiers import e2e_test


TEST_SERVICE_TYPE = 'ocean-meta-storage'
TEST_SERVICE_URL = 'http://localhost:8005'


@e2e_test
def test_did():
    test_id = '%s' % secrets.token_hex(32)

    valid_did = 'did:op:{0}'.format(test_id)

    assert DID().did.startswith(OCEAN_PREFIX)
    assert len(DID().did) - len(OCEAN_PREFIX) == 64

    with pytest.raises(TypeError):
        did_parse(None)

    # test invalid in bytes
    with pytest.raises(TypeError):
        assert did_parse(valid_did.encode())

    # test is_did_valid
    assert is_did_valid(valid_did)
    with pytest.raises(ValueError):
        is_did_valid('op:{}'.format(test_id))

    with pytest.raises(TypeError):
        is_did_valid(None)

    # test invalid in bytes
    with pytest.raises(TypeError):
        assert is_did_valid(valid_did.encode())

    valid_did_text = 'did:op:{}'.format(test_id)
    assert id_to_did(test_id) == valid_did_text

    # accept hex string from Web3 py
    assert id_to_did(Web3.toHex(hexstr=test_id)) == valid_did_text

    # accepts binary value
    assert id_to_did(Web3.toBytes(hexstr=test_id)) == valid_did_text

    with pytest.raises(TypeError):
        id_to_did(None)

    with pytest.raises(TypeError):
        id_to_did({'bad': 'value'})

    assert id_to_did('') == 'did:op:0'
    assert did_to_id(valid_did_text) == test_id
    assert did_to_id('did:op1:011') == '011'
    assert did_to_id('did:op:0') == '0'


@e2e_test
def test_did_to_bytes():
    id_test = secrets.token_hex(32)
    did_test = 'did:op:{}'.format(id_test)
    id_bytes = Web3.toBytes(hexstr=id_test)

    assert did_to_id_bytes(did_test) == id_bytes
    assert did_to_id_bytes(id_bytes) == id_bytes

    with pytest.raises(ValueError):
        assert did_to_id_bytes(id_test) == id_bytes

    with pytest.raises(ValueError):
        assert did_to_id_bytes('0x' + id_test)

    with pytest.raises(ValueError):
        did_to_id_bytes('did:opx:Somebadtexstwithnohexvalue0x123456789abcdecfg')

    with pytest.raises(ValueError):
        did_to_id_bytes('')

    with pytest.raises(TypeError):
        did_to_id_bytes(None)

    with pytest.raises(TypeError):
        did_to_id_bytes({})

    with pytest.raises(TypeError):
        did_to_id_bytes(42)
