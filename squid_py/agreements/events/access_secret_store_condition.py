import logging

from eth_utils import add_0x_prefix

from squid_py.did import did_to_id
from squid_py.keeper import Keeper
from squid_py.keeper.utils import process_tx_receipt

logger = logging.getLogger(__name__)


def fulfill_access_secret_store_condition(event, agreement_id, did, service_agreement,
                                          consumer_address, publisher_account):
    logger.debug(f"release reward after event {event}.")
    name_to_parameter = {param.name: param for param in
                         service_agreement.condition_by_name['accessSecretStore'].parameters}
    document_id = add_0x_prefix(name_to_parameter['_documentId'].value)
    asset_id = add_0x_prefix(did_to_id(did))
    assert document_id == asset_id, f'document_id {document_id} <=> asset_id {asset_id} mismatch.'
    try:
        Keeper.get_instance().unlock_account(publisher_account)
        tx_hash = Keeper.get_instance().access_secret_store_condition.fulfill(
            agreement_id, document_id, consumer_address, publisher_account
        )
        process_tx_receipt(
            tx_hash,
            Keeper.get_instance().access_secret_store_condition.FULFILLED_EVENT,
            'AccessSecretStoreCondition.Fulfilled'
        )
    except Exception as e:
        # logger.error(f'Error when calling grantAccess condition function: {e}')
        raise e


fulfillAccessSecretStoreCondition = fulfill_access_secret_store_condition
