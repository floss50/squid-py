import time

from blockchain.constants import OceanContracts
from blockchain.OceanContractsWrapper import OceanContractsWrapper
from acl.acl import generate_encryption_keys, decode, dec
from eth_account.messages import defunct_hash_message
import json
import requests

json_consume = {"publisherId": "0x01",
                "metadata": {
                    "name": "testzkp",
                    "links": ["https://testocnfiles.blob.core.windows.net/testfiles/testzkp.pdf"],
                    "size": "1.08MiB",
                    "format": "pdf",
                    "description": "description"
                },
                "assetId": "0x01"}
json_request_consume = {
    'requestId': "",
    'consumerId': "",
    'fixed_msg': "",
    'sigEncJWT': ""
}

ocean = OceanContractsWrapper()
ocean.init_contracts()

acl_concise = ocean.contracts[OceanContracts.OCEAN_ACL_CONTRACT][0]
acl = ocean.contracts[OceanContracts.OCEAN_ACL_CONTRACT][1]
market_concise = ocean.contracts[OceanContracts.OCEAN_MARKET_CONTRACT][0]
market = ocean.contracts[OceanContracts.OCEAN_MARKET_CONTRACT][1]
token = ocean.contracts[OceanContracts.OCEAN_TOKEN_CONTRACT][0]


def get_events(event_filter, max_iterations=100, pause_duration=0.1):
    events = event_filter.get_new_entries()
    i = 0
    while not events and i < max_iterations:
        i += 1
        time.sleep(pause_duration)
        events = event_filter.get_new_entries()

    if not events:
        print('no events found in %s events filter.' % str(event_filter))
    return events


def process_enc_token(event):
    # should get accessId and encryptedAccessToken in the event
    print("token published event: %s" % event)


def register():
    consumer_account = ocean.web3.eth.accounts[1]
    provider_account = ocean.web3.eth.accounts[0]
    print("Starting test_commit_access_requested")
    print("buyer: %s" % consumer_account)
    print("seller: %s" % provider_account)

    resource_id = market_concise.generateId('resource', transact={'from': provider_account})
    print("recource_id: %s" % resource_id)
    resource_price = 10
    json_consume['assetId'] = ocean.web3.toHex(resource_id)
    json_consume['links'] = ocean.web3.toHex(resource_id)
    headers = {'content-type': 'application/json'}
    post = requests.post('http://localhost:5000/api/v1/provider/assets/metadata',
                         data=json.dumps(json_consume),
                         headers=headers)
    return ocean.web3.toHex(resource_id)


def consume(resource):
    expire_seconds = 9999999999
    consumer_account = ocean.web3.eth.accounts[1]
    provider_account = ocean.web3.eth.accounts[0]
    resource_id = ocean.web3.toBytes(hexstr=resource)
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
    receipt = ocean.get_tx_receipt(req)
    send_event = acl.events.AccessConsentRequested().processReceipt(receipt)
    request_id = send_event[0]['args']['_id']

    filter_token_published = ocean.watch_event(OceanContracts.OACL, 'EncryptedTokenPublished', process_enc_token, 0.5,
                                               fromBlock='latest')

    i = 0
    while acl_concise.verifyCommitted(request_id, 1) is False and i < 100:
        i += 1
        time.sleep(0.1)

    assert acl_concise.verifyCommitted(request_id, 1)
    token.approve(ocean.web3.toChecksumAddress(market_concise.address),
                  resource_price,
                  transact={'from': consumer_account})
    send_payment = market_concise.sendPayment(request_id,
                                              provider_account,
                                              resource_price,
                                              expiry,
                                              transact={'from': consumer_account, 'gas': 6000000})

    receipt = ocean.get_tx_receipt(send_payment)
    send_event = acl.events.EncryptedTokenPublished().processReceipt(receipt)


    print('buyer balance = ', token.balanceOf(consumer_account))
    print('seller balance = ', token.balanceOf(provider_account))

    # tx_hashes = set()
    # events = get_events(filter_payment)
    # for ev in events:
    #     tx_hashes.add(ev['transactionHash'])

    # assert events
    # assert send_payment in tx_hashes

    events = get_events(filter_token_published)
    assert events
    assert events[0].args['_id'] == request_id
    on_chain_enc_token = events[0].args["_encryptedAccessToken"]

    signature = ocean.web3.eth.sign(consumer_account, data=on_chain_enc_token)

    fixed_msg = defunct_hash_message(hexstr=ocean.web3.toHex(on_chain_enc_token))

    decrypted_token = dec(on_chain_enc_token, privkey)

    sig = ocean.split_signature(signature)

    assert acl_concise.isSigned(consumer_account,
                                ocean.web3.toHex(fixed_msg),
                                sig.v,
                                sig.r,
                                sig.s,
                                call={'from': provider_account})
    json_request_consume['fixed_msg'] = ocean.web3.toHex(fixed_msg)
    json_request_consume['consumerId'] = consumer_account
    json_request_consume['sigEncJWT'] = ocean.web3.toHex(signature)
    json_request_consume['jwt'] = ocean.web3.toBytes(hexstr=ocean.web3.toHex(decrypted_token)).decode('utf-8')



    headers = {'content-type': 'application/json'}
    post = requests.post(
        'http://localhost:5000/api/v1/provider/assets/metadata/consume/%s' % ocean.web3.toHex(resource_id),
        data=json.dumps(json_request_consume), headers=headers)
    assert post.status_code == 200
    assert acl_concise.verifyCommitted(request_id, 2)


def test_commit_access_requested():
    asset1 = register()
    asset2 = register()
    consume(asset1)
    consume(asset2)

