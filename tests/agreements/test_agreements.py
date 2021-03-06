from squid_py import ConfigProvider
from squid_py.agreements.service_agreement import ServiceAgreement
from squid_py.keeper import Keeper
from squid_py.keeper.web3_provider import Web3Provider
from tests.resources.helper_functions import get_ddo_sample, log_event, get_consumer_account, get_publisher_account
from tests.resources.tiers import e2e_test


def setup_things():
    config = ConfigProvider.get_config()
    consumer_acc = get_consumer_account(config)
    publisher_acc = get_publisher_account(config)
    keeper = Keeper.get_instance()

    service_definition_id = 'Access'

    ddo = get_ddo_sample()
    keeper.did_registry.register(
        ddo.did,
        checksum=Web3Provider.get_web3().sha3(text=ddo.metadata['base']['checksum']),
        url='aquarius:5000',
        account=publisher_acc
    )

    registered_ddo = ddo
    asset_id = registered_ddo.asset_id
    service_agreement = ServiceAgreement.from_ddo(service_definition_id, ddo)
    agreement_id = ServiceAgreement.create_new_agreement_id()
    price = service_agreement.get_price()
    access_cond_id, lock_cond_id, escrow_cond_id = \
        service_agreement.generate_agreement_condition_ids(
            agreement_id, asset_id, consumer_acc.address, publisher_acc.address, keeper
        )

    return (
        keeper,
        publisher_acc,
        consumer_acc,
        agreement_id,
        asset_id,
        price,
        service_agreement,
        (lock_cond_id, access_cond_id, escrow_cond_id),
    )


@e2e_test
def test_escrow_access_secret_store_template_flow():
    """
    Test the agreement flow according to the EscrowAccessSecretStoreTemplate

    """
    (
        keeper,
        publisher_acc,
        consumer_acc,
        agreement_id,
        asset_id,
        price,
        service_agreement,
        (lock_cond_id, access_cond_id, escrow_cond_id),

    ) = setup_things()

    print('creating agreement:'
          'agrId: ', agreement_id,
          'asset_id', asset_id,
          '[lock_cond_id, access_cond_id, escrow_cond_id]', [lock_cond_id, access_cond_id, escrow_cond_id],
          'tlocks', service_agreement.conditions_timelocks,
          'touts', service_agreement.conditions_timeouts,
          'consumer', consumer_acc.address,
          'publisher', publisher_acc.address
          )

    try:
        proposed = keeper.template_manager.propose_template(keeper.escrow_access_secretstore_template.address, publisher_acc)
        print('template propose: ', proposed)
    except ValueError:
        print('propose template failed, maybe it is already proposed.')
        template_values = keeper.template_manager.get_template(keeper.escrow_access_secretstore_template.address)
        print('template values: ', template_values)

    owner_acc = publisher_acc
    try:
        approved = keeper.template_manager.approve_template(keeper.escrow_access_secretstore_template.address, owner_acc)
        print('template approve: ', approved)
    except ValueError:
        print(f'approve template from account {owner_acc.address} failed')

    assert keeper.template_manager.is_template_approved(keeper.escrow_access_secretstore_template.address), 'Template is not approved.'
    assert keeper.did_registry.get_block_number_updated(asset_id) > 0, 'asset id not registered'
    success = keeper.escrow_access_secretstore_template.create_agreement(
        agreement_id,
        asset_id,
        [access_cond_id, lock_cond_id, escrow_cond_id],
        service_agreement.conditions_timelocks,
        service_agreement.conditions_timeouts,
        consumer_acc.address,
        publisher_acc
    )
    print('create agreement: ', success)
    assert success, f'createAgreement failed {success}'
    event = keeper.escrow_access_secretstore_template.subscribe_agreement_created(
        agreement_id,
        10,
        log_event(keeper.escrow_access_secretstore_template.AGREEMENT_CREATED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for AgreementCreated '

    # Verify condition types (condition contracts)
    agreement = keeper.agreement_manager.get_agreement(agreement_id)
    assert agreement.did == asset_id, ''
    cond_types = keeper.escrow_access_secretstore_template.get_condition_types()
    for i, cond_id in enumerate(agreement.condition_ids):
        cond = keeper.condition_manager.get_condition(cond_id)
        assert cond.type_ref == cond_types[i]
        assert int(cond.state) == 1

    # Give consumer some tokens
    keeper.dispenser.request_tokens(price, consumer_acc)

    # Fulfill lock_reward_condition
    pub_token_balance = keeper.token.get_token_balance(publisher_acc.address)
    starting_balance = keeper.token.get_token_balance(keeper.escrow_reward_condition.address)
    keeper.token.token_approve(keeper.lock_reward_condition.address, price, consumer_acc)
    keeper.lock_reward_condition.fulfill(
        agreement_id, keeper.escrow_reward_condition.address, price, consumer_acc)
    event = keeper.lock_reward_condition.subscribe_condition_fulfilled(
        agreement_id,
        10,
        log_event(keeper.lock_reward_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for LockRewardCondition.Fulfilled'
    assert keeper.condition_manager.get_condition_state(lock_cond_id) == 2, ''
    assert keeper.token\
        .get_token_balance(keeper.escrow_reward_condition.address) == (price + starting_balance), ''

    # Fulfill access_secret_store_condition
    keeper.access_secret_store_condition.fulfill(
        agreement_id, asset_id, consumer_acc.address, publisher_acc)
    event = keeper.access_secret_store_condition.subscribe_condition_fulfilled(
        agreement_id,
        10,
        log_event(keeper.access_secret_store_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for AccessSecretStoreCondition.Fulfilled'
    assert keeper.condition_manager.get_condition_state(access_cond_id) == 2, ''

    # Fulfill escrow_reward_condition
    keeper.escrow_reward_condition.fulfill(
        agreement_id, price, publisher_acc.address,
        consumer_acc.address, lock_cond_id,
        access_cond_id, publisher_acc
    )
    event = keeper.escrow_reward_condition.subscribe_condition_fulfilled(
        agreement_id,
        10,
        log_event(keeper.escrow_reward_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for EscrowReward.Fulfilled'
    assert keeper.condition_manager.get_condition_state(escrow_cond_id) == 2, ''
    assert keeper.token\
        .get_token_balance(keeper.escrow_reward_condition.address) == starting_balance, ''
    assert keeper.token\
        .get_token_balance(publisher_acc.address) == (pub_token_balance + price), ''


@e2e_test
def test_agreement_hash(publisher_ocean_instance):
    """
    This test verifies generating agreement hash using fixed inputs and ddo example.
    This will make it easier to compare the hash generated from different languages.
    """
    w3 = Web3Provider.get_web3()
    did = "did:op:cb36cf78d87f4ce4a784f17c2a4a694f19f3fbf05b814ac6b0b7197163888865"
    template_id = w3.toChecksumAddress("0x00bd138abd70e2f00903268f3db08f2d25677c9e")
    agreement_id = '0xf136d6fadecb48fdb2fc1fb420f5a5d1c32d22d9424e47ab9461556e058fefaa'
    ddo = get_ddo_sample()

    sa = ServiceAgreement.from_service_dict(ddo.get_service(service_type='Access').as_dictionary())
    sa.service_agreement_template.set_template_id(template_id)
    assert template_id == sa.template_id, ''
    assert did == ddo.did
    # Don't generate condition ids, use fixed ids so we get consistent hash
    # (access_id, lock_id, escrow_id) = sa.generate_agreement_condition_ids(
    #     agreement_id, ddo.asset_id, consumer, publisher, keeper)
    access_id = '0x2d7c1d60dc0c3f52aa9bd71ffdbe434a0e58435571e64c893bc9646fea7f6ec1'
    lock_id = '0x1e265c434c14e668695dda1555088f0ea4356f596bdecb8058812e7dcba9ee73'
    escrow_id = '0xe487fa6d435c2f09ef14b65b34521302f1532ac82ba8f6c86116acd8566e2da3'
    print(f'condition ids: \n'
          f'{access_id} \n'
          f'{lock_id} \n'
          f'{escrow_id}')
    agreement_hash = ServiceAgreement.generate_service_agreement_hash(
        sa.template_id,
        (access_id, lock_id, escrow_id),
        sa.conditions_timelocks,
        sa.conditions_timeouts,
        agreement_id
    )
    print('agreement hash: ', agreement_hash.hex())
    expected = '0x96732b390dacec0f19ad304ac176b3407968a0184d01b3262687fd23a3f0995e'
    print('expected hash: ', expected)
    assert agreement_hash.hex() == expected, 'hash does not match.'
