"""
    DID Lib to do DID's and DDO's

"""

import re
import uuid
from eth_utils import remove_0x_prefix
from web3 import Web3

OCEAN_PREFIX = 'did:op:'


class DID:

    @property
    def did(self):
        """
        Create a did with the format did:op:cb36cf78d87f4ce4a784f17c2a4a694f19f3fbf05b814ac6b0b7197163888865

        :return: Asset did, str
        """
        return OCEAN_PREFIX + uuid.uuid4().hex + uuid.uuid4().hex


def did_parse(did):
    """
    Parse a DID into it's parts

    :param did: Asset did, str
    :return: Python dictionay with the method and the id.
    """
    if not isinstance(did, str):
        raise TypeError('Expecting DID of string type, got %s of %s type' % (did, type(did)))

    match = re.match('^did:([a-z0-9]+):([a-zA-Z0-9-.]+)(.*)', did)
    if not match:
        raise ValueError('DID %s does not seem to be valid.' % did)

    result = {
        'method': match.group(1),
        'id': match.group(2),
    }

    return result


def is_did_valid(did):
    """
    Return True if the did is a valid DID with the method name 'op' and the id
    in the Ocean format

    :param did: Asset did, str
    :return bool
    """
    result = did_parse(did)
    if result:
        return result['id'] is not None
    return False


def id_to_did(did_id, method='op'):
    """returns an Ocean DID from given a hex id"""
    if isinstance(did_id, bytes):
        did_id = Web3.toHex(did_id)

    # remove leading '0x' of a hex string
    if isinstance(did_id, str):
        did_id = remove_0x_prefix(did_id)
    else:
        raise TypeError("did id must be a hex string or bytes")

    # test for zero address
    if Web3.toBytes(hexstr=did_id) == b'':
        did_id = '0'
    return 'did:{0}:{1}'.format(method, did_id)


def did_to_id(did):
    """return an id extracted from a DID string"""
    result = did_parse(did)
    if result and result['id'] is not None:
        return result['id']
    return None


def did_to_id_bytes(did):
    """
    return an Ocean DID to it's correspondng hex id in bytes
    So did:op:<hex>, will return <hex> in byte format
    """
    if isinstance(did, str):
        if re.match('^[0x]?[0-9A-Za-z]+$', did):
            raise ValueError('{} must be a DID not a hex string'.format(did))
        else:
            did_result = did_parse(did)
            if not did_result:
                raise ValueError('{} is not a valid did'.format(did))
            if not did_result['id']:
                raise ValueError('{} is not a valid ocean did'.format(did))
            id_bytes = Web3.toBytes(hexstr=did_result['id'])
    elif isinstance(did, bytes):
        id_bytes = did
    else:
        raise TypeError(
            'Unknown did format, expected str or bytes, got {} of type {}'.format(did, type(did)))
    return id_bytes
