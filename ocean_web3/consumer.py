import time

from ocean_web3.constants import OceanContracts
from ocean_web3.acl import generate_encryption_keys, dec, decode
from eth_account.messages import defunct_hash_message
import json
import requests


def get_events(event_filter, max_iterations=100, pause_duration=0.1):
    events = event_filter.get_new_entries()
    i = 0
    while not events and i < max_iterations:
        i += 1
        time.sleep(pause_duration)
        events = event_filter.get_all_entries()

    if not events:
        print('no events found in %s events filter.' % str(event_filter))
    return events


def process_enc_token(event):
    # should get accessId and encryptedAccessToken in the event
    print("token published event: %s" % event)


def register(publisher_account, provider_account, price, ocean_contracts_wrapper, json_metadata,
             provider_host='http://localhost:5000'):
    if not bool(ocean_contracts_wrapper.contracts):
        ocean_contracts_wrapper.init_contracts()
    market_concise = ocean_contracts_wrapper.contracts[OceanContracts.OMKT][0]
    publisher_account = publisher_account
    provider_account = provider_account
    print("publisher: %s" % publisher_account)
    print("provider: %s" % provider_account)

    resource_id = market_concise.generateId('resource', transact={'from': provider_account})
    print("recource_id: %s" % resource_id)
    resource_price = price
    market_concise.register(resource_id,
                            resource_price,
                            transact={'from': provider_account})
    json_metadata['assetId'] = ocean_contracts_wrapper.web3.toHex(resource_id)
    headers = {'content-type': 'application/json'}
    post = requests.post(provider_host + '/api/v1/provider/assets/metadata',
                         data=json.dumps(json_metadata),
                         headers=headers)
    print("Metadata published with success")
    print("Resource published with resource_id: %s" % resource_id)
    return ocean_contracts_wrapper.web3.toHex(resource_id)


def consume(resource, consumer_account, provider_account, ocean_contracts_wrapper, json_metadata):
    if not bool(ocean_contracts_wrapper.contracts):
        ocean_contracts_wrapper.init_contracts()
    market_concise = ocean_contracts_wrapper.contracts[OceanContracts.OMKT][0]
    acl_concise = ocean_contracts_wrapper.contracts[OceanContracts.OACL][0]
    acl = ocean_contracts_wrapper.contracts[OceanContracts.OACL][1]
    token_concise = ocean_contracts_wrapper.contracts[OceanContracts.OTKN][0]

    expire_seconds = 9999999999
    consumer_account = consumer_account
    provider_account = provider_account
    resource_id = ocean_contracts_wrapper.web3.toBytes(hexstr=resource)
    resource_price = 10

    pubprivkey = generate_encryption_keys()
    pubkey = pubprivkey.public_key
    privkey = pubprivkey.private_key
    market_concise.requestTokens(2000, transact={'from': provider_account})
    market_concise.requestTokens(2000, transact={'from': consumer_account})
    expiry = int(time.time() + expire_seconds)
    req = acl_concise.initiateAccessRequest(resource_id,
                                            provider_account,
                                            pubkey,
                                            expiry,
                                            transact={'from': consumer_account})
    receipt = ocean_contracts_wrapper.get_tx_receipt(req)
    send_event = acl.events.AccessConsentRequested().processReceipt(receipt)
    request_id = send_event[0]['args']['_id']

    filter_token_published = ocean_contracts_wrapper.watch_event(OceanContracts.OACL, 'EncryptedTokenPublished',
                                                                 process_enc_token, 0.25,
                                                                 fromBlock='latest')

    i = 0
    while (acl_concise.statusOfAccessRequest(request_id) == 1) is False and i < 100:
        i += 1
        time.sleep(0.1)

    token_concise.approve(ocean_contracts_wrapper.web3.toChecksumAddress(market_concise.address),
                          resource_price,
                          transact={'from': consumer_account})
    send_payment = market_concise.sendPayment(request_id,
                                              provider_account,
                                              resource_price,
                                              expiry,
                                              transact={'from': consumer_account, 'gas': 6000000})

    events = get_events(filter_token_published)
    assert events[0].args['_id'] == request_id
    on_chain_enc_token = events[0].args["_encryptedAccessToken"]
    # on_chain_enc_token = acl_concise.getEncryptedAccessToken(request_id, call={'from': consumer_account})

    decrypted_token = dec(on_chain_enc_token, privkey)
    # pub_key = ocean.encoding_key_pair.public_key
    access_token = decode(decrypted_token)

    assert pubkey == access_token['temp_pubkey']
    signature = ocean_contracts_wrapper.web3.eth.sign(consumer_account, data=on_chain_enc_token)

    fixed_msg = defunct_hash_message(hexstr=ocean_contracts_wrapper.web3.toHex(on_chain_enc_token))

    sig = ocean_contracts_wrapper.split_signature(signature)

    json_metadata['fixed_msg'] = ocean_contracts_wrapper.web3.toHex(fixed_msg)
    json_metadata['consumerId'] = consumer_account
    json_metadata['sigEncJWT'] = ocean_contracts_wrapper.web3.toHex(signature)
    json_metadata['jwt'] = ocean_contracts_wrapper.web3.toBytes(
        hexstr=ocean_contracts_wrapper.web3.toHex(decrypted_token)).decode('utf-8')

    headers = {'content-type': 'application/json'}
    post = requests.post(
        access_token['service_endpoint'] + '/%s' % ocean_contracts_wrapper.web3.toHex(resource_id),
        data=json.dumps(json_metadata), headers=headers)
    return post
