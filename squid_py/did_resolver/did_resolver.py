"""DID Resolver Class."""
import logging

from squid_py.aquarius.aquarius_provider import AquariusProvider
from squid_py.did import did_to_id_bytes
from squid_py.did_resolver.resolver_value_type import ResolverValueType
from squid_py.exceptions import (
    OceanDIDUnknownValueType
)

logger = logging.getLogger('keeper')


class DIDResolver:
    """
    DID Resolver class
    Resolve DID to a URL/DDO.
    """

    def __init__(self, did_registry):
        self._did_registry = did_registry

    def resolve(self, did):
        """
        Resolve a DID to an URL/DDO or later an internal/external DID.

        :param did: 32 byte value or DID string to resolver, this is part of the ocean
            DID did:op:<32 byte value>
        :param max_hop_count: max number of hops allowed to find the destination URL/DDO
        :return string: URL or DDO of the resolved DID
        :return None: if the DID cannot be resolved
        :raises TypeError: if did has invalid format
        :raises TypeError: on non 32byte value as the DID
        :raises TypeError: on any of the resolved values are not string/DID bytes.
        :raises OceanDIDCircularReference: on the chain being pointed back to itself.
        :raises OceanDIDNotFound: if no DID can be found to resolve.
        """

        did_bytes = did_to_id_bytes(did)
        if not isinstance(did_bytes, bytes):
            raise TypeError('Invalid did: a 32 Byte DID value required.')

        # resolve a DID to a DDO
        url = self.get_resolve_url(did_bytes)
        logger.debug(f'found did {did} -> url={url}')
        return AquariusProvider.get_aquarius(url).get_asset_ddo(did)

    def get_resolve_url(self, did_bytes):
        """Return a did value and value type from the block chain event record using 'did'."""
        data = self._did_registry.get_registered_attribute(did_bytes)
        if not (data and data.get('value')):
            return None

        if data['value_type'] != ResolverValueType.URL:
            raise OceanDIDUnknownValueType(f'Unknown value type {data["value_type"]}')

        return data['value']
