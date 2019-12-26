"""
Exonum Client Module.

This module provides you with two handy classes:
  - ExonumClient: The main entity to interact with the Exonum blockchain.
  - Subscriber: An entity that can be used to receive signals on creation of a new block.
"""
from typing import Optional, Any, Callable, Union, Dict, Tuple

import json
from logging import getLogger
from threading import Thread
from urllib.parse import urlencode
from websocket import WebSocket

from .api import ServiceApi, PublicApi, PrivateApi, ProtobufApi
from .protobuf_loader import ProtobufLoader
from .message import ExonumMessage

# pylint: disable=C0103
logger = getLogger(__name__)


class Subscriber:
    """ Subscriber objects are used to subscribe to Exonum blocks via websockets. """

    # constants
    SUBSCRIPTION_WEBSOCKET_URI = "ws://{}:{}/api/explorer/v1/{}/subscribe"
    SENDING_WEBSOCKET_URI = "ws://{}:{}/api/explorer/v1/ws"
    SUBSCRIPTION_TYPES = ["blocks", "transactions"]

    # Type of the received data (it can be either bytes or a string).
    ReceiveType = Union[bytes, str]
    # Type of the `Callback` (`Callable` that takes `ReceiveType` as an argument and produces nothing).
    CallbackType = Callable[[ReceiveType], None]

    def __init__(
        self, address: str, port: int, subscription_type: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
    ):
        """Subscriber constructor.

        Parameters
        ----------
        address: str
            IP address of the Exonum node.
        port: int
            Port of the exonum node.
        subscription_type: Optional[str]
            Type of subscription: "blocks" or "transactions". If not given,
            it is assumed that subscriber is used to send transactions.
        filters: Optional[Dict[str, Any]]
            Dictionary of filters, such as 'service_id' and 'tx_id' for transactions.
        """
        if not subscription_type:
            self._address = self.SENDING_WEBSOCKET_URI.format(address, port)
        else:
            if subscription_type not in Subscriber.SUBSCRIPTION_TYPES:
                err = ValueError(
                    f"Subscription type must be one of these: {self.SUBSCRIPTION_TYPES}, "
                    f"while {subscription_type} is given."
                )
                logger.error("Error occurred during subscriber initialization: %s", err)
                raise err
            parameters = "?" + urlencode(filters) if filters else ""
            self._address = self.SUBSCRIPTION_WEBSOCKET_URI.format(address, port, subscription_type) + parameters
        self._is_running = False
        self._connected = False
        self._ws_client = WebSocket()
        self._thread = Thread(target=self._event_processing)
        self._handler: Optional[Subscriber.CallbackType] = None

    def __enter__(self) -> "Subscriber":
        self.connect()

        return self

    def __exit__(self, exc_type: Optional[type], exc_value: Optional[Any], exc_traceback: Optional[object]) -> None:
        self.stop()

    def connect(self) -> None:
        """Connects the subscriber to the Exonum, so it will be able to receive events. """
        self._ws_client.connect(self._address)
        self._connected = True

    def set_handler(self, handler: "Subscriber.CallbackType") -> None:
        """Sets the handler """
        self._handler = handler

    def run(self) -> None:
        """Runs the subscriber thread. It will call the provided handler on every new block. """
        try:
            self._is_running = True
            self._thread.setDaemon(True)
            self._thread.start()
            logger.debug("Subscriber thread started successfully.")
        except RuntimeError as error:
            logger.error("Error occurred during running subscriber thread: %s", error)

    def _event_processing(self) -> None:
        while self._is_running:
            data = self._ws_client.recv()
            if data and self._handler:
                self._handler(data)

    def wait_for_new_event(self) -> None:
        """ Waits until a new event (block or transaction) is ready. Please note that this method is a blocking one. """
        if self._is_running:
            print("Subscriber is already running...")
        else:
            self._ws_client.recv()

    def stop(self) -> None:
        """Closes connection with the websocket and, if the thread is running, joins it. """
        if self._is_running:
            self._is_running = False

        if self._connected:
            self._ws_client.close()
            self._connected = False

        if self._thread.is_alive():
            self._thread.join()

    def send_transaction(self, message: ExonumMessage) -> str:
        """
        Sends a transaction into an Exonum node via WebSocket.
        Example:
        >>> response = client.send_websocket_transaction(message)
        >>> print(response)
        {"result":"success","response":{"tx_hash":"48b7d71d388f3c2dfa665bcf837e1fa0417ca559fb0163533ea72de6319e61ca"}}
        Parameters
        ----------
        message: ExonumMessage
            Prepared and signed an Exonum message.
        Returns
        -------
        result: str
            Result of the WebSocket request.
            If a transaction is correct and it is accepted, it will contain a JSON with a hash of the transaction.
        """
        body_raw = message.signed_raw()
        if body_raw is None:
            logger.critical("Attempt to send an unsigned message through websocket.")
            raise RuntimeError("Attempt to send an unsigned message.")
        data = json.dumps({"type": "transaction", "payload": {"tx_body": body_raw.hex()}})

        ws_client = WebSocket()
        ws_client.connect(self._address)
        ws_client.send(data)
        response = ws_client.recv()
        ws_client.close()

        return response


class ExonumClient:
    """ExonumClient class is capable of interaction with ExonumBlockchain.

    All the methods that perform requests to the Exonum REST API return a requests.Response object.
    So a user should manually verify that the status code of the request is correct and get the contents
    of the request via `response.json()`.

    Since ExonumClient uses `requests` library for the communication, user should expect that every
    method that performs an API call can raise a `requests` exception (e.g. `requests.exceptions.ConnectionError`).

    Example usage:

    >>> client = ExonumClient(hostname="127.0.0.1", public_api_port=8080, private_api_port=8081)
    >>> health_info = client.public_api.health_info().json()
    {'consensus_status': 'Enabled', 'connected_peers': 0}
    >>> user_agent = client.public_api.user_agent().json()
    exonum 0.13.0-rc.2/rustc 1.37.0 (eae3437df 2019-08-13)
    """

    def __init__(self, hostname: str, public_api_port: int = 80, private_api_port: int = 81, ssl: bool = False):
        """
        Constructor of ExonumClient.

        Parameters
        ----------
        hostname: str
            Examples: '127.0.0.1', 'www.some_node.com'.
        public_api_port: int
            Public API port of an Exonum node.
        private_api_port: int
            Private API port of an Exonum node.
        ssl: bool
            If True, HTTPS protocol is used for communication, otherwise HTTP is used.
        """
        self.schema = "https" if ssl else "http"
        self.hostname = hostname
        self.public_api_port = public_api_port
        self.private_api_port = private_api_port

        self.public_api = PublicApi(hostname, public_api_port, self.schema)
        self.private_api = PrivateApi(hostname, private_api_port, self.schema)
        self.protobuf_api = ProtobufApi(hostname, public_api_port, self.schema)

    def __repr__(self) -> str:
        """ Conversion to a string. """
        d = {
            "object": f"<{self.__class__.__name__} instance at {id(self)}>",
            "host": self.hostname,
            "public_port": str(self.public_api_port),
            "private_port": str(self.private_api_port),
        }

        return json.dumps(d, indent=2)

    def service_private_api(self, service_name: str) -> ServiceApi:
        """Creates an instances of ServiceApi to interact with private API of a service.

        Parameters
        ----------
        service_name: str
            Name of a service.

        Returns
        -------
        service_api: ServiceApi
            An instance of ServiceApi for private API.
        """
        return ServiceApi(service_name, self.hostname, self.private_api_port, self.schema)

    def service_public_api(self, service_name: str) -> ServiceApi:
        """Creates an instances of ServiceApi to interact with public API of a service.

        Parameters
        ----------
        service_name: str
            Name of a service.

        Returns
        -------
        service_api: ServiceApi
            An instance of ServiceApi for public API.
        """
        return ServiceApi(service_name, self.hostname, self.public_api_port, self.schema)

    def service_apis(self, service_name: str) -> Tuple[ServiceApi, ServiceApi]:
        """Creates a tuple of ServiceApi instances to interact with public and private API of a service.

        Parameters
        ----------
        service_name: str
            Name of a service.

        Returns
        -------
        service_apis: (ServiceApi, ServiceApi)
            Tuple of ServiceApi instances: first for public API and second for private.
        """
        return self.service_public_api(service_name), self.service_private_api(service_name)

    def protobuf_loader(self) -> ProtobufLoader:
        """
        Creates a ProtobufLoader from the current ExonumClient object.

        See ProtobufLoader docs for more details.

        Example:

        >>> with client.protobuf_loader("blocks") as loader:
        >>>     loader.load_main_proto_files()
        >>>     loader.load_service_proto_files(0, "exonum-supervisor:0.13.0-rc.2")
        """
        return ProtobufLoader(self.protobuf_api)

    def create_subscriber(self, subscription_type: str) -> Subscriber:
        """
        Creates a Subscriber object from the current ExonumClient object.

        See Subscriber docs for details.

        Example:

        >>> with client.create_subscriber("blocks") as subscriber:
        >>>     subscriber.wait_for_new_event()

        Parameters
        ----------
        subscription_type: str
            Sets type of subscription: "blocks" or "transactions".
        """
        subscriber = Subscriber(self.hostname, self.public_api_port, subscription_type)
        return subscriber
