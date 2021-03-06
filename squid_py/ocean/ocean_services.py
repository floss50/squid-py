"""Ocean module."""
from squid_py.agreements.service_factory import ServiceDescriptor


class OceanServices:
    """Ocean services class."""

    @staticmethod
    def create_access_service(price, service_endpoint, consume_endpoint, timeout=None):
        """
        Publish an asset with an `Access` service according to the supplied attributes.

        :param price: int price of service in ocean tokendids
        :param service_endpoint: str URL for initiating service access request
        :param consume_endpoint: str URL to consume service
        :param timeout: int amount of time in seconds before the agreement expires
        :return: Service instance or None
        """
        timeout = timeout or 3600  # default to one hour timeout
        service = ServiceDescriptor.access_service_descriptor(
            price, service_endpoint, consume_endpoint, timeout, ''
        )

        return service
