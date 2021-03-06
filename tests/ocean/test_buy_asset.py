import os

from secret_store_client.client import RPCError

from squid_py.agreements.service_agreement import ServiceAgreement
from squid_py.agreements.service_types import ServiceTypes
from squid_py.config_provider import ConfigProvider
from squid_py.ddo.ddo import DDO
from examples import ExampleConfig
from squid_py.keeper import Keeper
from squid_py.keeper.web3_provider import Web3Provider
from tests.resources.helper_functions import (
    get_account_from_config,
    get_registered_ddo,
    get_publisher_account,
    log_event)


def test_buy_asset(consumer_ocean_instance, publisher_ocean_instance):
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)
    keeper = Keeper.get_instance()
    # :TODO: enable the actual SecretStore
    # SecretStoreProvider.set_secret_store_class(SecretStore)
    w3 = Web3Provider.get_web3()
    pub_acc = get_publisher_account(config)
    # publisher_ocean_instance.templates.propose(keeper.escrow_access_secretstore_template.address,publisher_ocean_instance.main_account)
    # publisher_ocean_instance.templates.approve(keeper.escrow_access_secretstore_template.address,publisher_ocean_instance.main_account)


    # Register ddo
    ddo = get_registered_ddo(publisher_ocean_instance, pub_acc)
    assert isinstance(ddo, DDO)
    # ocn here will be used only to publish the asset. Handling the asset by the publisher
    # will be performed by the Brizo server running locally

    cons_ocn = consumer_ocean_instance
    # restore the http client because we want the actual Brizo server to do the work
    # not the BrizoMock.
    # Brizo.set_http_client(requests)
    consumer_account = get_account_from_config(cons_ocn._config, 'parity.address1',
                                               'parity.password1')

    downloads_path_elements = len(
        os.listdir(consumer_ocean_instance._config.downloads_path)) if os.path.exists(
        consumer_ocean_instance._config.downloads_path) else 0
    # sign agreement using the registered asset did above
    service = ddo.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    assert ServiceAgreement.SERVICE_DEFINITION_ID in service.as_dictionary()
    sa = ServiceAgreement.from_service_dict(service.as_dictionary())
    # This will send the purchase request to Brizo which in turn will execute the agreement on-chain
    cons_ocn.accounts.request_tokens(consumer_account, 100)
    agreement_id = cons_ocn.assets.order(
        ddo.did, sa.service_definition_id, consumer_account)

    event = keeper.escrow_access_secretstore_template.subscribe_agreement_created(
        agreement_id,
        20,
        log_event(keeper.escrow_access_secretstore_template.AGREEMENT_CREATED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for EscrowAccessSecretStoreTemplate.AgreementCreated'

    event = keeper.lock_reward_condition.subscribe_condition_fulfilled(
        agreement_id,
        20,
        log_event(keeper.lock_reward_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for LockRewardCondition.Fulfilled'

    event = keeper.escrow_reward_condition.subscribe_condition_fulfilled(
        agreement_id,
        10,
        log_event(keeper.escrow_reward_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for EscrowReward.Fulfilled'

    assert w3.toHex(event.args['_agreementId']) == agreement_id
    assert len(os.listdir(config.downloads_path)) == downloads_path_elements + 1

    # decrypt the contentUrls using the publisher account instead of consumer account.
    # if the secret store is working and ACL check is enabled, this should fail
    # since SecretStore decrypt will fail the checkPermissions check
    try:
        cons_ocn.assets.consume(
            agreement_id, ddo.did, service.service_definition_id, pub_acc, config.downloads_path
        )
    except RPCError:
        print('hooray, secret store is working as expected.')
