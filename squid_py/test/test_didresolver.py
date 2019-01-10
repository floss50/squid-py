import logging
import math
import secrets

import pytest
from web3 import Web3

from squid_py.ddo import DDO
from squid_py.did import id_to_did


from squid_py.did_resolver import (
    DIDResolver,
)
from squid_py.exceptions import (
    OceanDIDCircularReference,
    OceanDIDNotFound,
)
from squid_py.keeper.web3_provider import Web3Provider
from squid_py.models.resolver_value_type import ResolverValueType
from ..test_resources.tiers import e2e_test


logger = logging.getLogger()


@e2e_test
def test_did_registry_register(publisher_ocean_instance):
    ocean = publisher_ocean_instance

    register_account = ocean.main_account
    # owner_address = register_account.address
    did_registry = ocean.keeper.did_registry
    did_id = secrets.token_hex(32)
    did_test = 'did:op:' + did_id
    key_test = Web3.sha3(text='provider')
    value_test = 'http://localhost:5000'

    # register DID-> URL
    did_registry.register(did_test, url=value_test, key=key_test, account=register_account)

    # register DID-> DDO Object
    ddo = DDO(did_test)
    ddo.add_signature()
    ddo.add_service('metadata-test', value_test)

    did_registry.register(did_test, ddo=ddo, key=key_test, account=register_account)

    # register DID-> DDO json
    did_registry.register(did_test, ddo=ddo.as_text(), account=register_account)

    # register DID-> DID string
    did_id_new = secrets.token_hex(32)
    did_test_new = 'did:op:' + did_id_new
    did_registry.register(did_test, did=did_test_new, account=register_account)

    # register DID-> DID bytes
    did_registry.register(did_test, did=Web3.toBytes(hexstr=did_id_new), account=register_account)

    # test circular ref
    with pytest.raises(OceanDIDCircularReference):
        did_registry.register(did_test, did=did_test, account=register_account)

    # No account provided
    with pytest.raises(ValueError):
        did_registry.register(did_test, url=value_test)

    # Invalide key field provided
    with pytest.raises(ValueError):
        did_registry.register(did_test, url=value_test, account=register_account, key=42)


@e2e_test
def test_did_resolver_library(publisher_ocean_instance):
    ocean = publisher_ocean_instance
    register_account = ocean.main_account
    owner_address = register_account.address
    did_registry = ocean.keeper.did_registry
    did_id = secrets.token_hex(32)
    did_test = 'did:op:' + did_id
    value_type = ResolverValueType.URL
    key_test = Web3.sha3(text='provider')
    value_test = 'http://localhost:5000'
    key_zero = Web3.toBytes(hexstr='0x' + ('00' * 32))

    did_resolver = DIDResolver(Web3Provider.get_web3(), ocean.keeper.did_registry)

    # resolve URL from a direct DID ID value
    did_id_bytes = Web3.toBytes(hexstr=did_id)

    did_registry.register(did_test, url=value_test, account=register_account)

    did_resolved = did_resolver.resolve(did_test)
    assert did_resolved
    assert did_resolved.is_url
    assert did_resolved.url == value_test
    assert did_resolved.key == key_zero
    assert did_resolved.owner == owner_address

    with pytest.raises(ValueError):
        did_resolver.resolve(did_id)

    did_resolved = did_resolver.resolve(did_id_bytes)
    assert did_resolved
    assert did_resolved.is_url
    assert did_resolved.url == value_test
    assert did_resolved.key == key_zero
    assert did_resolved.owner == owner_address

    # resolve URL from a hash of a DID string
    did_hash = Web3.sha3(text=did_test)

    register_account.unlock()
    register_did = did_registry.register_attribute(did_hash, value_type, key_test, value_test,
                                                   owner_address)
    receipt = did_registry.get_tx_receipt(register_did)
    gas_used_url = receipt['gasUsed']
    did_resolved = did_resolver.resolve(did_hash)
    assert did_resolved
    assert did_resolved.is_url
    assert did_resolved.url == value_test
    assert did_resolved.key == key_test
    assert did_resolved.value_type == value_type
    assert did_resolved.owner == owner_address
    assert did_resolved.block_number == receipt['blockNumber']

    # test update of an already assigned DID
    value_test_new = 'http://aquarius:5000'
    register_account.unlock()
    register_did = did_registry.register_attribute(did_hash, value_type, key_test, value_test_new,
                                                   owner_address)
    receipt = did_registry.get_tx_receipt(register_did)
    did_resolved = did_resolver.resolve(did_hash)
    assert did_resolved
    assert did_resolved.is_url
    assert did_resolved.url == value_test_new
    assert did_resolved.key == key_test
    assert did_resolved.value_type == value_type
    assert did_resolved.owner == owner_address
    assert did_resolved.block_number == receipt['blockNumber']

    # resolve DDO from a direct DID ID value
    ddo = DDO(did_test)
    ddo.add_signature()
    ddo.add_service('meta-store', value_test)
    did_id = secrets.token_hex(32)
    did_id_bytes = Web3.toBytes(hexstr=did_id)
    value_type = ResolverValueType.DDO

    register_account.unlock()
    register_did = did_registry.register_attribute(did_id_bytes, value_type, key_test,
                                                   ddo.as_text(), owner_address)
    receipt = did_registry.get_tx_receipt(register_did)
    gas_used_ddo = receipt['gasUsed']

    did_resolved = did_resolver.resolve(did_id_bytes)
    resolved_ddo = DDO(json_text=did_resolved.ddo)

    assert did_resolved
    assert did_resolved.is_ddo
    assert ddo.calculate_hash() == resolved_ddo.calculate_hash()
    assert did_resolved.key == key_test
    assert did_resolved.value_type == value_type
    assert did_resolved.owner == owner_address
    assert did_resolved.block_number == receipt['blockNumber']

    logger.info('gas used URL: %d, DDO: %d, DDO +%d extra', gas_used_url, gas_used_ddo,
                gas_used_ddo - gas_used_url)

    value_type = ResolverValueType.URL
    # resolve chain of direct DID IDS to URL
    chain_length = 4
    ids = []
    for i in range(0, chain_length):
        ids.append(secrets.token_hex(32))

    for i in range(0, chain_length):
        did_id_bytes = Web3.toBytes(hexstr=ids[i])
        register_account.unlock()
        if i < len(ids) - 1:
            next_did_id = Web3.toHex(hexstr=ids[i + 1])
            logger.debug('add chain {0} -> {1}'.format(Web3.toHex(did_id_bytes), next_did_id))
            register_did = did_registry.register_attribute(
                did_id_bytes, ResolverValueType.DID, key_test, next_did_id, owner_address)
        else:
            logger.debug('end chain {0} -> URL'.format(Web3.toHex(did_id_bytes)))
            register_did = did_registry.register_attribute(
                did_id_bytes, ResolverValueType.URL, key_test, value_test, owner_address)

        receipt = did_registry.get_tx_receipt(register_did)

    did_id_bytes = Web3.toBytes(hexstr=ids[0])
    did_resolved = did_resolver.resolve(did_id_bytes)
    assert did_resolved
    assert did_resolved.is_url
    assert did_resolved.url == value_test
    assert did_resolved.hop_count == chain_length
    assert did_resolved.key == key_test
    assert did_resolved.value_type == value_type
    assert did_resolved.owner == owner_address
    assert did_resolved.block_number == receipt['blockNumber']

    # test circular chain

    # get the did at the end of the chain
    did_id_bytes = Web3.toBytes(hexstr=ids[len(ids) - 1])
    # make the next DID at the end of the chain to point to the first DID
    next_did_id = Web3.toHex(hexstr=ids[0])
    register_account.unlock()
    logger.debug('set end chain {0} -> {1}'.format(Web3.toHex(did_id_bytes), next_did_id))
    register_did = did_registry.register_attribute(did_id_bytes, ResolverValueType.DID, key_test, next_did_id, owner_address)
    did_registry.get_tx_receipt(register_did)
    # get the first DID in the chain
    did_id_bytes = Web3.toBytes(hexstr=ids[0])
    with pytest.raises(OceanDIDCircularReference):
        did_resolver.resolve(did_id_bytes)

    # test hop count
    hop_count = math.floor(len(ids) / 2)
    did_resolved = did_resolver.resolve(did_id_bytes, hop_count)
    assert did_resolved
    assert did_resolved.is_did
    assert did_resolved.did == id_to_did(Web3.toHex(hexstr=ids[hop_count]))

    # test DID not found
    did_id = secrets.token_hex(32)
    did_id_bytes = Web3.toBytes(hexstr=did_id)
    with pytest.raises(OceanDIDNotFound):
        did_resolver.resolve(did_id_bytes)

    # test value type error on a linked DID
    register_account.unlock()
    register_did = did_registry.register_attribute(
        did_id_bytes, ResolverValueType.DID, key_test, value_test, owner_address)

    did_registry.get_tx_receipt(register_did)

    # resolve to get the error
    with pytest.raises(Exception):
        did_resolver.resolve(did_id_bytes)

    # test value type error on a linked DID_REF
    register_account.unlock()
    register_did = did_registry.register_attribute(
        did_id_bytes, ResolverValueType.DID_REF, key_test, value_test, owner_address)
    did_registry.get_tx_receipt(register_did)

    # resolve to get the error
    with pytest.raises(Exception):
        did_resolver.resolve(did_id_bytes)
