"""
Aquarius module.
Help to communicate with the metadata store.
"""
import json
import logging

import requests

from squid_py.aquarius.exceptions import AquariusGenericError
from squid_py.assets.asset import Asset

logger = logging.getLogger('aquarius')


class Aquarius:
    """Aquarius wrapper to call different endpoint of aquarius component."""

    def __init__(self, aquarius_url):
        """
        The Metadata class is a wrapper on the Metadata Store, which has exposed a REST API.

        :param aquarius_url: Url of the aquarius instance.
        """
        # :HACK:
        if '/api/v1/aquarius/assets' in aquarius_url:
            aquarius_url = aquarius_url[:aquarius_url.find('/api/v1/aquarius/assets')]

        self._base_url = f'{aquarius_url}/api/v1/aquarius/assets'
        self._headers = {'content-type': 'application/json'}

        logging.debug(f'Metadata Store connected at {aquarius_url}')
        logging.debug(f'Metadata Store API documentation at {aquarius_url}/api/v1/docs')
        logging.debug(f'Metadata assets at {self._base_url}')

    @property
    def url(self):
        """Base URL of the aquarius instance."""
        return f'{self._base_url}/ddo'

    def get_service_endpoint(self, did):
        """
        Retrieve the endpoint with the ddo for a given did.

        :param did: Asset DID string
        :return: Return the url of the the ddo location
        """
        return f'{self.url}/{did}'

    def list_assets(self):
        """
        List all the assets registered in the aquarius instance.

        :return: List of DID string
        """
        response = requests.get(self._base_url).content
        if not response:
            return {}

        try:
            asset_list = json.loads(response)
        except TypeError:
            asset_list = None
        except ValueError:
            raise ValueError(response.decode('UTF-8'))

        if not asset_list:
            return []

        if 'ids' in asset_list:
            return asset_list['ids']
        return []

    def get_asset_ddo(self, did):
        """
        Retrieve asset ddo for a given did.

        :param did: Asset DID string
        :return: DDO instance
        """
        response = requests.get(f'{self.url}/{did}').content
        if not response:
            return {}
        try:
            parsed_response = json.loads(response)
        except TypeError:
            parsed_response = None
        except ValueError:
            raise ValueError(response.decode('UTF-8'))
        if parsed_response is None:
            return {}
        return Asset(dictionary=parsed_response)

    def get_asset_metadata(self, did):
        """
        Retrieve asset metadata for a given did.

        :param did: Asset DID string
        :return: metadata key of the DDO instance
        """
        response = requests.get(f'{self._base_url}/metadata/{did}').content
        if not response:
            return {}
        try:
            parsed_response = json.loads(response)
        except TypeError:
            parsed_response = None
        except ValueError:
            raise ValueError(response.decode('UTF-8'))
        if parsed_response is None:
            return {}
        return parsed_response['metadata']

    def list_assets_ddo(self):
        """
        List all the ddos registered in the aquarius instance.

        :return: List of DDO instance
        """
        return json.loads(requests.get(self.url).content)

    def publish_asset_ddo(self, ddo):
        """
        Register asset ddo in aquarius.

        :param ddo: DDO instance
        :return: API response (depends on implementation)
        """
        try:
            asset_did = ddo.did
            response = requests.post(self.url, data=ddo.as_text(),
                                     headers=self._headers)
        except AttributeError:
            raise AttributeError('DDO invalid. Review that all the required parameters are filled.')
        if response.status_code == 500:
            raise ValueError(
                f'This Asset ID already exists! \n\tHTTP Error message: \n\t\t{response.text}')
        elif response.status_code != 201:
            raise Exception(f'{response.status_code} ERROR Full error: \n{response.text}')
        elif response.status_code == 201:
            response = json.loads(response.content)
            logger.debug(f'Published asset DID {asset_did}')
            return response
        else:
            raise Exception(f'Unhandled ERROR: status-code {response.status_code}, '
                            f'error message {response.text}')

    def update_asset_ddo(self, did, ddo):
        """
        Update the ddo of a did already registered.

        :param did: Asset DID string
        :param ddo: DDO instance
        :return: API response (depends on implementation)
        """
        response = requests.put(f'{self.url}/{did}', data=ddo.as_text(),
                                headers=self._headers)
        if response.status_code == 200 or response.status_code == 201:
            return json.loads(response.content)
        else:
            raise Exception(f'Unable to update DDO: {response.content}')

    def text_search(self, text, sort=None, offset=100, page=0):
        """
        Search in aquarius using text query.

        Given the string aquarius will do a full-text query to search in all documents.

        Currently implemented are the MongoDB and Elastic Search drivers.

        For a detailed guide on how to search, see the MongoDB driver documentation:
        mongodb driverCurrently implemented in:
        https://docs.mongodb.com/manual/reference/operator/query/text/

        And the Elastic Search documentation:
        https://www.elastic.co/guide/en/elasticsearch/guide/current/full-text-search.html
        Other drivers are possible according to each implementation.

        :param text: String to be search.
        :param sort: 1/-1 to sort ascending or descending.
        :param offset: Integer with the number of elements displayed per page.
        :param page: Integer with the number of page.
        :return: List of DDO instance
        """
        payload = {"text": text, "sort": sort, "offset": offset, "page": page}
        response = requests.get(
            f'{self.url}/query',
            params=payload,
            headers=self._headers
        )
        if response.status_code == 200:
            return self._parse_search_response(response.content)
        else:
            raise Exception(f'Unable to search for DDO: {response.content}')

    def query_search(self, search_query):
        """
        Search using a query.

        Currently implemented is the MongoDB query model to search for documents according to:
        https://docs.mongodb.com/manual/tutorial/query-documents/

        And an Elastic Search driver, which implements a basic parser to convert the query into
        elastic search format.

        Example: query_search({"service.metadata.base.name":"London Weather 2011"})

        :param search_query: Python dictionary, query following mongodb syntax
        :return: List of DDO instance
        """
        response = requests.post(
            f'{self.url}/query',
            data=json.dumps(search_query),
            headers=self._headers
        )
        if response.status_code == 200:
            return self._parse_search_response(response.content)
        else:
            raise Exception(f'Unable to search for DDO: {response.content}')

    def retire_asset_ddo(self, did):
        """
        Retire asset ddo of Aquarius.

        :param did: Asset DID string
        :return: API response (depends on implementation)
        """
        response = requests.delete(f'{self.url}/{did}', headers=self._headers)
        if response.status_code == 200:
            logging.debug(f'Removed asset DID: {did} from metadata store')
            return response

        raise AquariusGenericError(f'Unable to remove DID: {response}')

    def validate_metadata(self, metadata):
        """
        Validate that the metadata of your ddo is valid.

        :param metadata: Json dict
        :return: bool
        """
        response = requests.post(
            f'{self.url}/validate',
            data=json.dumps(metadata),
            headers=self._headers
        )
        if response.content == b'true\n':
            return True
        else:
            logger.info(self._parse_search_response(response.content))
            return False

    @staticmethod
    def _parse_search_response(response):
        if not response:
            return {}
        try:
            parsed_response = json.loads(response)
        except TypeError:
            parsed_response = None

        if parsed_response is None:
            return []
        elif isinstance(parsed_response, list):
            return parsed_response
        else:
            raise ValueError(
                f'Unknown search response, expecting a list got {type(parsed_response)}.')
