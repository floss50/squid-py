"""
    Test ocean class

"""
import logging
import os
import time

import requests
import pytest
from web3 import Web3
from secret_store_client.client import Client

from squid_py.ddo import DDO
from squid_py.ddo.metadata import Metadata
from squid_py.did import DID, did_to_id
from squid_py.exceptions import OceanDIDNotFound
from squid_py.keeper.utils import get_fingerprint_by_name
from squid_py.keeper.web3_provider import Web3Provider
from squid_py.ocean.brizo import Brizo
from squid_py.ocean.secret_store import SecretStore
from squid_py.service_agreement.utils import build_condition_key
from squid_py.test_resources.mocks.brizo_mock import BrizoMock
from squid_py.utils.utilities import generate_new_id, prepare_prefixed_hash
from squid_py.modules.v0_1.accessControl import grantAccess
from squid_py.modules.v0_1.payment import lockPayment, releasePayment
from squid_py.modules.v0_1.serviceAgreement import fulfillAgreement
from squid_py.ocean.asset import Asset
from squid_py.service_agreement.service_agreement import ServiceAgreement
from squid_py.service_agreement.service_factory import ServiceDescriptor
from squid_py.service_agreement.service_types import ServiceTypes
from squid_py.test_resources.helper_functions import get_registered_ddo, get_publisher_ocean_instance, get_resource_path
from ...test_resources.tiers import e2e_test


def print_config(ocean_instance):
    print("Ocean object configuration:".format())
    print("Ocean.config.keeper_path: {}".format(ocean_instance.config.keeper_path))
    print("Ocean.config.keeper_url: {}".format(ocean_instance.config.keeper_url))
    print("Ocean.config.gas_limit: {}".format(ocean_instance.config.gas_limit))
    print("Ocean.config.aquarius_url: {}".format(ocean_instance.config.aquarius_url))


@e2e_test
def test_ocean_instance(publisher_ocean_instance):
    print_config(publisher_ocean_instance)
    assert publisher_ocean_instance.keeper.token is not None

    print_config(publisher_ocean_instance)


@e2e_test
def test_accounts(publisher_ocean_instance):
    for address in publisher_ocean_instance.accounts:
        print(publisher_ocean_instance.accounts[address])

    # These accounts have a positive ETH balance
    for address, account in publisher_ocean_instance.accounts.items():
        assert account.ether_balance >= 0
        assert account.ocean_balance >= 0


@e2e_test
def test_token_request(publisher_ocean_instance, consumer_ocean_instance):
    amount = 2000

    pub_ocn = publisher_ocean_instance
    cons_ocn = consumer_ocean_instance
    # Get the current accounts, assign 2

    # Start balances for comparison
    aquarius_start_eth = pub_ocn.main_account.ether_balance
    aquarius_start_ocean = pub_ocn.main_account.ocean_balance

    # Make requests, assert success on request
    rcpt = pub_ocn.main_account.request_tokens(amount)
    Web3Provider.get_web3().eth.waitForTransactionReceipt(rcpt)
    rcpt = cons_ocn.main_account.request_tokens(amount)
    Web3Provider.get_web3().eth.waitForTransactionReceipt(rcpt)

    # Update and print balances
    # Ocean.accounts is a dict address: account
    for address in pub_ocn.accounts:
        print(pub_ocn.accounts[address])
    aquarius_current_eth = pub_ocn.main_account.ether_balance
    aquarius_current_ocean = pub_ocn.main_account.ocean_balance

    # Confirm balance changes
    assert pub_ocn.main_account.balance.eth == aquarius_current_eth
    assert pub_ocn.main_account.balance.ocn == aquarius_current_ocean
    # assert aquarius_current_eth < aquarius_start_eth
    # assert aquarius_current_ocean == aquarius_start_ocean + amount


@e2e_test
def test_register_asset(publisher_ocean_instance):
    logging.debug("".format())
    asset_price = 100
    sample_ddo_path = get_resource_path('ddo', 'ddo_sample2.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    ##########################################################
    # Setup account
    ##########################################################
    publisher = publisher_ocean_instance.main_account

    # ensure Ocean token balance
    if publisher.ocean_balance == 0:
        rcpt = publisher.request_tokens(200)
        Web3Provider.get_web3().eth.waitForTransactionReceipt(rcpt)

    # You will need some token to make this transfer!
    assert publisher.ocean_balance > 0

    ##########################################################
    # Create an Asset with valid metadata
    ##########################################################
    asset = Asset.from_ddo_json_file(sample_ddo_path)

    ######################

    # For this test, ensure the asset does not exist in Aquarius
    meta_data_assets = publisher_ocean_instance.metadata_store.list_assets()
    if asset.ddo.did in meta_data_assets:
        publisher_ocean_instance.metadata_store.get_asset_ddo(asset.ddo.did)
        publisher_ocean_instance.metadata_store.retire_asset_ddo(asset.ddo.did)

    ##########################################################
    # Register using high-level interface
    ##########################################################
    service_descriptors = [
        ServiceDescriptor.access_service_descriptor(asset_price, '/purchaseEndpoint',
                                                    '/serviceEndpoint', 600,
                                                    ('0x%s' % generate_new_id()))]
    publisher_ocean_instance.register_asset(asset.metadata, publisher, service_descriptors)


@e2e_test
def test_resolve_did(publisher_ocean_instance):
    # prep ddo
    metadata = Metadata.get_example()
    publisher = publisher_ocean_instance.main_account
    original_ddo = publisher_ocean_instance.register_asset(
        metadata, publisher,
        [ServiceDescriptor.access_service_descriptor(7, '/dummy/url', '/service/endpoint', 3,
                                                     ('0x%s' % generate_new_id()))]
    )

    # happy path
    did = original_ddo.did
    ddo = publisher_ocean_instance.resolve_did(did).as_dictionary()
    original = original_ddo.as_dictionary()
    assert ddo['publicKey'] == original['publicKey']
    assert ddo['authentication'] == original['authentication']
    assert ddo['service'][:-1] == original['service'][:-1]
    # assert ddo == original_ddo.as_dictionary(), 'Resolved ddo does not match original.'

    # Can't resolve unregistered asset
    unregistered_did = DID().did
    with pytest.raises(OceanDIDNotFound, message='Expected OceanDIDNotFound error.'):
        publisher_ocean_instance.resolve_did(unregistered_did)

    # Raise error on bad did
    invalid_did = "did:op:0123456789"
    with pytest.raises(OceanDIDNotFound,
                       message='Expected a OceanDIDNotFound error when resolving invalid did.'):
        publisher_ocean_instance.resolve_did(invalid_did)


@e2e_test
def test_sign_agreement(publisher_ocean_instance, consumer_ocean_instance, registered_ddo):
    # assumptions:
    #  - service agreement template must already be registered
    #  - asset ddo already registered

    consumer = consumer_ocean_instance.main_account.address

    # point consumer_ocean_instance's brizo mock to the publisher's ocean instance
    Brizo.set_http_client(BrizoMock(publisher_ocean_instance))
    # sign agreement using the registered asset did above
    service = registered_ddo.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    assert ServiceAgreement.SERVICE_DEFINITION_ID_KEY in service.as_dictionary()
    sa = ServiceAgreement.from_service_dict(service.as_dictionary())

    service_agreement_id = consumer_ocean_instance.sign_service_agreement(
        registered_ddo.did,
        sa.sa_definition_id,
        consumer
    )
    assert service_agreement_id, 'agreement id is None.'
    print('got new service agreement id:', service_agreement_id)
    filter1 = {'serviceAgreementId': Web3.toBytes(hexstr=service_agreement_id)}
    filter_2 = {'serviceId': Web3.toBytes(hexstr=service_agreement_id)}
    executed = wait_for_event(
        consumer_ocean_instance.keeper.service_agreement.events.ExecuteAgreement, filter1)
    assert executed
    locked = wait_for_event(consumer_ocean_instance.keeper.payment_conditions.events.PaymentLocked,
                            filter_2)
    assert locked
    granted = wait_for_event(consumer_ocean_instance.keeper.access_conditions.events.AccessGranted,
                             filter_2)
    assert granted
    released = wait_for_event(
        consumer_ocean_instance.keeper.payment_conditions.events.PaymentReleased, filter_2)
    assert released
    fulfilled = wait_for_event(
        consumer_ocean_instance.keeper.service_agreement.events.AgreementFulfilled, filter1)
    assert fulfilled
    print('agreement was fulfilled.')


@e2e_test
def test_execute_agreement(publisher_ocean_instance, consumer_ocean_instance, registered_ddo):
    """
    This tests execute agreement without going through Ocean's sign agreement / execute agreement
    functions so we can bypass the event handling watchers.
    In this test we invoke all of the conditions directly in the expected order and also check
    for the emitted events to verify that the keeper contracts are working correctly.

    """
    consumer_ocn = consumer_ocean_instance
    keeper = consumer_ocn.keeper
    web3 = Web3Provider.get_web3()
    consumer_acc = consumer_ocn.main_account
    publisher_acc = publisher_ocean_instance.main_account
    service_index = '0'
    did = registered_ddo.did

    # sign agreement
    agreement_id, service_agreement, service_def, ddo = consumer_ocn._get_service_agreement_to_sign(
        did, service_index)

    consumer_ocn.main_account.unlock()
    signature, sa_hash = service_agreement.get_signed_agreement_hash(
        agreement_id, consumer_acc
    )
    # Must approve token transfer for this purchase
    consumer_ocn._approve_token_transfer(service_agreement.get_price())

    # execute the agreement
    pub_ocn = publisher_ocean_instance
    asset_id = did_to_id(ddo.did)
    ddo, service_agreement, service_def = pub_ocn._get_ddo_and_service_agreement(ddo.did,
                                                                                 service_index)
    pub_ocn.keeper.service_agreement.execute_service_agreement(
        service_agreement.template_id,
        signature,
        consumer_acc.address,
        service_agreement.conditions_params_value_hashes,
        service_agreement.conditions_timeouts,
        agreement_id,
        asset_id,
        pub_ocn.main_account
    )

    filter1 = {'serviceAgreementId': Web3.toBytes(hexstr=agreement_id)}
    filter_2 = {'serviceId': Web3.toBytes(hexstr=agreement_id)}

    # WAIT FOR ####### ExecuteAgreement Event
    executed = wait_for_event(pub_ocn.keeper.service_agreement.events.ExecuteAgreement, filter1)
    assert executed, ''
    cons = keeper.service_agreement.get_service_agreement_consumer(agreement_id)
    pub = keeper.service_agreement.get_service_agreement_publisher(agreement_id)
    assert cons == consumer_acc.address
    assert pub == publisher_acc.address

    cond = service_agreement.conditions[0]
    fn_fingerprint = get_fingerprint_by_name(keeper.payment_conditions.contract.abi,
                                             cond.function_name)
    sa_contract = keeper.service_agreement.contract_concise
    pay_cont_address = keeper.payment_conditions.address

    terminated = sa_contract.isAgreementTerminated(agreement_id)
    assert terminated is False
    template_id = web3.toHex(sa_contract.getTemplateId(agreement_id))
    assert template_id == service_agreement.template_id

    k = build_condition_key(pay_cont_address, web3.toBytes(hexstr=fn_fingerprint),
                            service_agreement.template_id)
    cond_key = web3.toHex(
        sa_contract.getConditionByFingerprint(agreement_id, pay_cont_address, fn_fingerprint))
    assert k == cond_key, 'problem with condition keys: %s vs %s' % (k, cond_key)
    assert cond_key == service_agreement.conditions_keys[0]

    pay_status = sa_contract.getConditionStatus(agreement_id, service_agreement.conditions_keys[0])
    assert pay_status == 0, 'lockPayment condition should be 0 at this point.'
    pay_has_dependencies = sa_contract.hasUnfulfilledDependencies(agreement_id,
                                                                  service_agreement.conditions_keys[
                                                                      0])
    assert pay_has_dependencies is False

    # Lock payment
    lockPayment(web3, keeper.artifacts_path, consumer_acc, agreement_id, service_def)
    # WAIT FOR ####### PaymentLocked event
    locked = wait_for_event(keeper.payment_conditions.events.PaymentLocked, filter_2)
    # assert locked, ''
    if not locked:
        lock_cond_status = keeper.service_agreement.contract_concise.getConditionStatus(
            agreement_id,
            service_agreement.conditions_keys[
                0])
        assert lock_cond_status > 0
        grant_access_cond_status = keeper.service_agreement.contract_concise.getConditionStatus(
            agreement_id,
            service_agreement.conditions_keys[
                1])
        release_cond_status = keeper.service_agreement.contract_concise.getConditionStatus(
            agreement_id,
            service_agreement.conditions_keys[
                2])
        assert grant_access_cond_status == 0 and release_cond_status == 0, 'grantAccess and/or releasePayment is fulfilled but not expected to.'

    # Grant access
    grantAccess(web3, keeper.artifacts_path, publisher_acc, agreement_id, service_def)
    # WAIT FOR ####### AccessGranted event
    granted = wait_for_event(keeper.access_conditions.events.AccessGranted, filter_2)
    assert granted, ''
    # Release payment
    releasePayment(web3, keeper.artifacts_path, publisher_acc, agreement_id, service_def)
    # WAIT FOR ####### PaymentReleased event
    released = wait_for_event(keeper.payment_conditions.events.PaymentReleased, filter_2)
    assert released, ''
    # Fulfill agreement
    fulfillAgreement(web3, keeper.artifacts_path, publisher_acc, agreement_id, service_def)
    # Wait for ####### AgreementFulfilled event (verify agreement was fulfilled)
    fulfilled = wait_for_event(keeper.service_agreement.events.AgreementFulfilled, filter1)
    assert fulfilled, ''
    print('All good.')
    # Repeat execute test but with a refund payment (i.e. don't grant access)


def wait_for_event(event, arg_filter, wait_iterations=20):
    _filter = event.createFilter(fromBlock=0, argument_filters=arg_filter)
    for check in range(wait_iterations):
        events = _filter.get_all_entries()
        if events:
            return events[0]
        time.sleep(0.5)


@e2e_test
def test_agreement_hash(publisher_ocean_instance):
    """
    This test verifies generating agreement hash using fixed inputs and ddo example.
    This will make it easier to compare the hash generated from different languages.
    """
    did = "did:op:0xcb36cf78d87f4ce4a784f17c2a4a694f19f3fbf05b814ac6b0b7197163888865"
    # user_address = "0x00bd138abd70e2f00903268f3db08f2d25677c9e"
    template_id = "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
    service_agreement_id = '0xf136d6fadecb48fdb2fc1fb420f5a5d1c32d22d9424e47ab9461556e058fefaa'
    print('sid: ', service_agreement_id)
    ddo_file_name = 'shared_ddo_example.json'

    file_path = get_resource_path('ddo', ddo_file_name)
    ddo = DDO(json_filename=file_path)

    service = ddo.get_service(service_type='Access')
    service = service.as_dictionary()
    sa = ServiceAgreement.from_service_dict(service)
    service[ServiceAgreement.SERVICE_CONDITIONS_KEY] = [cond.as_dictionary() for cond in
                                                        sa.conditions]
    assert template_id == sa.template_id, ''
    assert did == ddo.did
    agreement_hash = ServiceAgreement.generate_service_agreement_hash(
        sa.template_id, sa.conditions_keys,
        sa.conditions_params_value_hashes, sa.conditions_timeouts, service_agreement_id
    )
    print('agreement hash: ', agreement_hash.hex())
    print('expected hash: ', "0x66652d0f8f8ec464e67aa6981c17fa1b1644e57d9cfd39b6f1b58ad1b71d61bb")
    assert agreement_hash.hex() == "0x66652d0f8f8ec464e67aa6981c17fa1b1644e57d9cfd39b6f1b58ad1b71d61bb", 'hash does not match.'


@e2e_test
def test_verify_signature(consumer_ocean_instance):
    """
    squid-py currently uses `web3.eth.sign()` to sign the service agreement hash. This signing method
    uses ethereum `eth_sign` on the ethereum client which automatically prepends the
    message with text defined in EIP-191 as version 'E': `b'\\x19Ethereum Signed Message:\\n'`
    concatenated with the number of bytes in the message.

    It is more convenient to sign a message using `web3.eth.sign()` because it only requires the account address
    whereas `web3.eth.account.signHash()` requires a private_key to sign the message.
    `web3.eth.account.signHash()` also does not prepend anything to the message before signing.
    Messages signed via Metamask in pleuston use the latter method and current fail to verify in squid-py/brizo.
    The signature verification fails because recoverHash is being used on a prepended message but the signature
    created by `web3.eth.account.signHash()` does not add a prefix before signing.

    """
    ocn = consumer_ocean_instance
    w3 = Web3Provider.get_web3()

    def verify_signature(_address, _agreement_hash, _signature, expected_match):
        prefixed_hash = prepare_prefixed_hash(_agreement_hash)
        recovered_address0 = w3.eth.account.recoverHash(prefixed_hash, signature=_signature)
        recovered_address1 = w3.eth.account.recoverHash(_agreement_hash, signature=_signature)
        print('original address: ', _address)
        print('w3.eth.account.recoverHash(prefixed_hash, signature=signature)  => ',
              recovered_address0)
        print('w3.eth.account.recoverHash(agreement_hash, signature=signature) => ',
              recovered_address1)
        assert _address == (recovered_address0, recovered_address1)[expected_match], \
            'Could not verify signature using address {}'.format(_address)

    # Signature created from Metamask (same as using `web3.eth.account.signHash()`)
    address = '0x8248039e67801Ac0B9d0e38201E963194abdb540'
    hex_agr_hash = '0xc8ea6bf6f4f4e2bf26a645dd4a1be20f5151c74964026c36efc2149bfae5f924'
    agreement_hash = Web3.toBytes(hexstr=hex_agr_hash)
    assert hex_agr_hash == '0x' + agreement_hash.hex()
    signature = (
        '0x200ce6aa55f0b4080c5f3a5dbe8385d2d196b0380cbdf388f79b6b004223c68a4f7972deb36417df8599155da2f903e43fe7e7eb40214db6bd6e55fd4c4fcf2a1c'
    )
    verify_signature(address, agreement_hash, signature, 1)

    # Signature created using `web3.eth.sign()` (squid-py, squid-js with no metamask)
    address = "0x00Bd138aBD70e2F00903268F3Db08f2D25677C9e"
    hex_agr_hash = "0xeeaae0098b39fdf8fab6733152dd0ef54729ac486f9846450780c5cc9d44f5e8"
    agreement_hash = Web3.toBytes(hexstr=hex_agr_hash)
    signature = (
        "0x44fa549d33f5993f73e96f91cad01d9b37830da78494e35bda32a280d1b864ac020a761e872633c8149a5b63b65a1143f9f5a3be35822a9e90e0187d4a1f9d101c"
    )
    assert hex_agr_hash == '0x' + agreement_hash.hex()
    verify_signature(address, agreement_hash, signature, 0)


@e2e_test
def test_consume_flow(consumer_ocean_instance):
    # This test requires all services running including:
    # secret store
    # parity node
    # aquarius
    # brizo
    # mongodb/bigchaindb

    return
    pub_ocn = get_publisher_ocean_instance()

    # restore the proper http requests client and secret store client
    Brizo.set_http_client(requests)
    # pub_ocn._http_client = requests
    SecretStore.set_client(Client)

    # Register ddo
    ddo = get_registered_ddo(pub_ocn)
    # did = 'did:op:0x96a49018357a4a1e9f179a3a746af5a087559b4ca133499198428dc4b0868731'
    # ddo = consumer_ocean_instance.resolve_did(did)

    path = os.path.join(consumer_ocean_instance._downloads_path, 'testfiles')
    consumer_ocean_instance._downloads_path = path

    # pub_ocn here will be used only to publish the asset. Handling the asset by the publisher
    # will be performed by the Brizo server running locally

    consumer = consumer_ocean_instance.main_account.address

    # sign agreement using the registered asset did above
    service = ddo.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    assert ServiceAgreement.SERVICE_DEFINITION_ID_KEY in service.as_dictionary()
    sa = ServiceAgreement.from_service_dict(service.as_dictionary())
    # This will send the purchase request to Brizo which in turn will execute the agreement on-chain
    service_agreement_id = consumer_ocean_instance.sign_service_agreement(ddo.did,
                                                                          sa.sa_definition_id,
                                                                          consumer)
    print('got new service agreement id:', service_agreement_id)
    filter1 = {'serviceAgreementId': Web3.toBytes(hexstr=service_agreement_id)}
    filter_2 = {'serviceId': Web3.toBytes(hexstr=service_agreement_id)}

    executed = wait_for_event(
        consumer_ocean_instance.keeper.service_agreement.events.ExecuteAgreement, filter1)
    assert executed
    granted = wait_for_event(consumer_ocean_instance.keeper.access_conditions.events.AccessGranted,
                             filter_2)
    assert granted
    fulfilled = wait_for_event(
        consumer_ocean_instance.keeper.service_agreement.events.AgreementFulfilled, filter1)
    assert fulfilled

    path = consumer_ocean_instance._downloads_path
    # check consumed data file in the downloads folder
    assert os.path.exists(path), ''
    folder_names = os.listdir(path)
    assert folder_names, ''
    for name in folder_names:
        asset_path = os.path.join(path, name)
        if os.path.isfile(asset_path):
            continue

        filenames = os.listdir(asset_path)
        assert filenames, 'no files created in this dir'
        assert os.path.isfile(os.path.join(asset_path, filenames[0])), ''

    print('agreement was fulfilled.')
    import shutil
    shutil.rmtree(consumer_ocean_instance._downloads_path)
