"""
Exonum Client Module.

This module provides you with two handy classes:
  - ExonumClient: The main entity to interact with the Exonum blockchain.
  - Subscriber: An entity that can be used to receive signals on creation of a new block.
"""
from typing import Optional, Any, Callable, Union, Iterable, List, Dict

import json
from logging import getLogger
from threading import Thread
from urllib.parse import urlencode
from websocket import WebSocket
import requests

from .protobuf_loader import ProtobufLoader, ProtobufProviderInterface, ProtoFile
from .message import ExonumMessage

# pylint: disable=C0103
logger = getLogger(__name__)

RUST_RUNTIME_ID = 0

# Example of a formatted prefix: "https://127.0.0.1:8000"
_ENDPOINT_PREFIX = "{}://{}:{}"

_RUST_RUNTIME_URL = _ENDPOINT_PREFIX + "/api/runtimes/rust/{}"
_TX_URL = _ENDPOINT_PREFIX + "/api/explorer/v1/transactions"
_BLOCK_URL = _ENDPOINT_PREFIX + "/api/explorer/v1/block"
_BLOCKS_URL = _ENDPOINT_PREFIX + "/api/explorer/v1/blocks"
_SYSTEM_URL = _ENDPOINT_PREFIX + "/api/system/v1/{}"
_SERVICE_URL = _ENDPOINT_PREFIX + "/api/services/{}/"
_SUBSCRIPTION_WEBSOCKET_URI = "ws://{}:{}/api/explorer/v1/{}/subscribe"
_SENDING_WEBSOCKET_URI = "ws://{}:{}/api/explorer/v1/ws"
_SUBSCRIPTION_TYPES = ["blocks", "transactions"]


class Subscriber:
    """ Subscriber objects are used to subscribe to Exonum blocks via websockets. """

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
            self._address = _SENDING_WEBSOCKET_URI.format(address, port)
        else:
            if subscription_type not in _SUBSCRIPTION_TYPES:
                err = ValueError(
                    f"Subscription type must be one of these: {_SUBSCRIPTION_TYPES}, "
                    f"while {subscription_type} is given."
                )
                logger.error("Error occurred during subscriber initialization: %s", err)
                raise err
            parameters = "?" + urlencode(filters) if filters else ""
            self._address = _SUBSCRIPTION_WEBSOCKET_URI.format(address, port, subscription_type) + parameters
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

        if self._thread.isAlive():
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


# pylint: disable=too-many-public-methods
class ExonumClient(ProtobufProviderInterface):
    """ExonumClient class is capable of interaction with ExonumBlockchain.

    All the methods that perform requests to the Exonum REST API return a requests.Response object.
    So a user should manually verify that the status code of the request is correct and get the contents
    of the request via `response.json()`.

    Since ExonumClient uses `requests` library for the communication, user should expect that every
    method that performs an API call can raise a `requests` exception (e.g. `requests.exceptions.ConnectionError`).

    Example usage:

    >>> client = ExonumClient(hostname="127.0.0.1", public_api_port=8080, private_api_port=8081)
    >>> health_info = client.health_info().json()
    {'consensus_status': 'Enabled', 'connected_peers': 0}
    >>> user_agent = client.user_agent().json()
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
        self.tx_url = _TX_URL.format(self.schema, hostname, public_api_port)

    def __repr__(self) -> str:
        """ Conversion to a string. """
        d = {
            "object": f"<{self.__class__.__name__} instance at {id(self)}>",
            "host": self.hostname,
            "public_port": str(self.public_api_port),
            "private_port": str(self.private_api_port),
        }

        return json.dumps(d, indent=2)

    def protobuf_loader(self) -> ProtobufLoader:
        """
        Creates a ProtobufLoader from the current ExonumClient object.

        See ProtobufLoader docs for more details.

        Example:

        >>> with client.protobuf_loader("blocks") as loader:
        >>>     loader.load_main_proto_files()
        >>>     loader.load_service_proto_files(0, "exonum-supervisor:0.13.0-rc.2")
        """
        return ProtobufLoader(self)

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

    def service_endpoint(self, service_name: str, sub_uri: str, private: bool = False) -> str:
        """
        Creates a service endpoint for a given service name and sub-uri.

        Example:

        >>> client.service_endpoint("supervisor", "deploy-artifact", private=True)
        http://127.0.0.1:8081/api/services/supervisor/deploy-artifact

        Parameters
        ----------
        service_name: str
            Name of a service instance.
        sub_uri: str
            Additional part of a URL to be added to the endpoint, e.g. "some/sub/uri?parameter=value"
        private: bool
            Denotes if a private port should be used. Defaults to False.

        Returns
        -------
        url: str
            Returns a service REST API URL based on the provided parameters.
        """
        port = self.public_api_port if not private else self.private_api_port

        service_url = _SERVICE_URL.format(self.schema, self.hostname, port, service_name)

        return service_url + sub_uri

    # API section.
    # Methods below perform REST API calls to an Exonum node:

    def available_services(self) -> requests.Response:
        """
        Gets a list of available services from Exonum.

        Example:

        >>> available_services = client.available_services().json()
        >>> print(json.dumps(available_services, indent=2))
        {
          "artifacts": [
            {
              "runtime_id": 0,
              "name": "exonum-supervisor",
              "version": "0.13.0-rc.2"
            }
          ],
          "services": [
            {
              "spec": {
                "id": 0,
                "name": "supervisor",
                "artifact": {
                  "runtime_id": 0,
                  "name": "exonum-supervisor",
                  "version": "0.13.0-rc.2"
                }
              },
              "status": "Active"
            }
          ]
        }
        """
        return _get(self._system_public_endpoint("services"))

    def get_instance_id_by_name(self, name: str) -> Optional[int]:
        """
        Gets an ID of the service instance with the provided name.

        Example:

        >>> id = client.get_instance_id_by_name("cryptocurrency")
        >>> id
        42

        Parameters
        ----------
        name: Name of the service.

        Returns
        -------
        result: int
            ID of the instance.

        Raises
        ------
        RuntimeError
            An error will be raised if a response code is not 200.
        """
        response = self.available_services()

        if response.status_code != 200:
            raise RuntimeError("Couldn't get info about available services")

        available_services = response.json()

        for state in available_services["services"]:
            service = state["spec"]
            if service["name"] == name:
                return service["id"]

        return None

    def send_transaction(self, message: ExonumMessage) -> requests.Response:
        """
        Sends a transaction into an Exonum node via REST API.

        Example:

        >>> response = client.send_transaction(message)
        >>> response.json()
        {'tx_hash': '713de312f48fe15559c0d4f7fb3f274dfbd3893a8a80d9f4224e97248f0e314e'}

        Parameters
        ----------
        message: ExonumMessage
            Prepared and signed an Exonum message.

        Returns
        -------
        result: requests.Response
            Result of the POST request.
            If a transaction is correct and it is accepted, it will contain a JSON with a hash of the transaction.
        """
        response = _post(self.tx_url, data=message.pack_into_json(), headers={"content-type": "application/json"})
        return response

    def send_transactions(self, messages: Iterable[ExonumMessage]) -> List[requests.Response]:
        """
        Same as send_transaction, but for any iterable object over ExonumMessage.

        Parameters
        ----------
        messages: Iterable[ExonumMessage]
            A sequence of messages to send.

        Returns
        -------
        results: List[requests.Response]
            A list of responses for each sent transaction.
        """
        return [self.send_transaction(message) for message in messages]

    def get_block(self, height: int) -> requests.Response:
        """
        Gets a block at the provided height.

        Example:

        >>> block = client.get_block(2).json()
        >>> print(json.dumps(block, indent=2))
        {
          "proposer_id": 0,
          "height": 2,
          "tx_count": 0,
          "prev_hash": "e686088d5323e51c096b42126a65fff59363c740ad0d8260c6c03c2e0c40ecdd",
          "tx_hash": "c6c0aa07f27493d2f2e5cff56c890a353a20086d6c25ec825128e12ae752b2d9",
          "state_hash": "e552443214f22721d007f1eef03f5e4d2483c31a439043eb32cd7b1faeef354f",
          "precommits": [
            "0a5c2...0603"
          ],
          "txs": [],
          "time": "2019-09-12T09:50:49.390408335Z"
        }

        Parameters
        ----------
        height: int
            A height of the required block.

        Returns
        -------
        block_response: requests.Response
            Result of an API call.
            If it is successful, a JSON representation of the block will be in the response.
        """
        return _get(_BLOCK_URL.format(self.schema, self.hostname, self.public_api_port), params={"height": height})

    # pylint: disable=too-many-arguments
    def get_blocks(
        self,
        count: int,
        earliest: Optional[int] = None,
        latest: Optional[int] = None,
        add_precommits: bool = False,
        skip_empty_blocks: bool = False,
        add_blocks_time: bool = False,
    ) -> requests.Response:
        """
        Gets a range of blocks.

        Blocks will be returned in a reversed order starting from the latest to the `latest - count + 1`.
        See the `latest` parameter description for details.

        Parameters
        ----------
        count: int
            Amount of blocks. Should not be greater than Exonum's parameter MAX_BLOCKS_PER_REQUEST
        earliest: Optional[int]
            If not provided, it is considered to be the height of the earliest block in the blockchain.
            Otherwise, a provided value will be used.
        latest: Optional[int]
            If not provided, it is considered to be the height of the latest block in the blockchain.
            Otherwise, a provided value will be used.
        add_precommits: bool
            If True, precommits will also be taken into account.
        skip_empty_blocks: bool
            If True, only non-empty blocks will be returned. By default it is False.
        add_blocks_time: bool
            If True, then the returned `times` field of BlockRange will contain a median time from the
            corresponding block precommits.

        Returns
        -------
        blocks_range_response: requests.Response
            Result of an API call.
            If it is successful, a JSON representation of the block range will be in the response.
        """
        blocks_url = _BLOCKS_URL.format(self.schema, self.hostname, self.public_api_port)
        params: Dict[str, Union[int, str]] = dict()
        params["count"] = count

        if earliest:
            params["earliest"] = earliest
        if latest:
            params["latest"] = latest
        if add_precommits:
            params["add_precommits"] = "true"
        if skip_empty_blocks:
            params["skip_empty_blocks"] = "true"
        if add_blocks_time:
            params["add_blocks_time"] = "true"

        return _get(blocks_url, params=params)

    def get_tx_info(self, tx_hash: str) -> requests.Response:
        """
        Gets information about the transaction with the provided hash.

        Example:

        >>> tx_info = client.get_tx_info(tx_hash).json()
        >>> print(json.dumps(tx_info, indent=2))
        {
          'type': 'committed',
          'content': '0a11...660d',
          'location': {
            'block_height': 58224,
            'position_in_block': 1
          },
          'location_proof': {
            'proof': [
              {
                'index': 0,
                'height': 1,
                'hash': '14637aa10b700cebfbc23d45395e8677d1fe1914d2e7f50d38cf1b73cfba1702'
              }
            ],
            'entries': [
              [1, 'e2d9ba5e8e104d65be8d3af7c26e5abea8f27da280cea110a80c9ab4f4d2a10c']
            ],
            'length': 2
          },
          'status': {
            'type': 'success'
          },
          'time': '2019-09-12T13:08:10.528537286Z'
        }

        Parameters
        ----------
        tx_hash: str
            A hexadecimal representation of the transaction hash.

        Returns
        -------
        block_response: requests.Response
            Result of an API call.
            If it is successful, a JSON representation of the transaction info will be in the response.
        """
        return _get(_TX_URL.format(self.schema, self.hostname, self.public_api_port), params={"hash": tx_hash})

    def get_service(self, service_name: str, sub_uri: str, private: bool = False) -> requests.Response:
        """
        Performs a GET request to the endpoint generated by the `service_endpoint` method.

        Parameters are the same as in `service_endpoint`.

        Returns
        -------
        response: requests.Response
            Result of an API call.
        """
        return _get(self.service_endpoint(service_name, sub_uri, private))

    def post_service(self, service_name: str, sub_uri: str, data: str, private: bool = False) -> requests.Response:
        """
        Performs a POST request to the endpoint generated by the `service_endpoint` method.

        Parameters are the same as in `service_endpoint` except for `data`.
        `data` is expected to be a serialized JSON value.

        Returns
        -------
        response: requests.Response
            Result of an API call.
        """
        json_headers = {"content-type": "application/json"}
        return _post(self.service_endpoint(service_name, sub_uri, private), data=data, headers=json_headers)

    def health_info(self) -> requests.Response:
        """ Performs a GET request to the healthcheck Exonum endpoint. """
        return _get(self._system_public_endpoint("healthcheck"))

    def stats(self) -> requests.Response:
        """ Performs a GET request to the stats Exonum endpoint. """
        return _get(self._system_public_endpoint("stats"))

    def user_agent(self) -> requests.Response:
        """ Performs a GET request to the user_agent Exonum endpoint. """
        return _get(self._system_public_endpoint("user_agent"))

    def add_peer(self, address: str, public_key: str) -> requests.Response:
        """
        Performs a POST request to the '{system_base_path}/peers' endpoint in order to add a new peer to the node.

        Parameters
        ----------
        address: IP address of the node which the present node should connect to.
        public_key: public key of the node which the present node should connect to.

        Returns
        -------
        response: requests.Response
            Result of an API call.
        """
        data = json.dumps({"address": address, "public_key": public_key})
        response = _post(
            self._system_private_endpoint("peers"), data=data, headers={"content-type": "application/json"}
        )
        return response

    def get_peers(self) -> requests.Response:
        """
        Performs a GET request to the '{system_base_path}/peers' to get a list of peers of the node.

        Example:

        >>> peers = client.get_peers().json()
        >>> print(json.dumps(peers, indent=2))
        {
          "incoming_connections": [{
            "address": "127.0.0.1:57671",
            "public_key": "8a17bdfe42c10abdb7f27b5648691db3338400c27812e847e02eb7193ad490f2"
          }],
          "outgoing_connections": {
            "127.0.0.1:6334": {
              "public_key": "dcb46dceaeb7d0eab7b6ed000f317f2ab9f7c8423ec9a6a602d81c0979e1333a",
              "state": {
                "type": "Active"
              }
            },
            "127.0.0.1:6335": {
              "public_key": "dcb46dceaeb7d0eab7b6ed000f317f2ab9f7c8423ec9a6a602d81c0979e1333a",
              "state": {
                "delay": 4000,
                "type": "Reconnect"
              }
            },
            "127.0.0.1:6336": {
              "public_key": null,
              "state": {
                "type": "Active"
              }
            },
            "127.0.0.1:6337": {
              "public_key": null,
              "state": {
                "delay": 4000,
                "type": "Reconnect"
              }
            }
          }
        }

        Returns
        -------
        response: requests.Response
            Result of an API call.
            If it is successful, a list of peers will be returned.
        """
        return _get(self._system_private_endpoint("peers"))

    def set_consensus_interaction(self, enabled: bool = True) -> requests.Response:
        """
        Performs a POST request to the '{system_base_path}/consensus_enabled'
        to switch consensus interaction of the node on or off.

        Parameters
        ----------
        enabled: flag that switches consensus interaction of the node on (True) or off (False).

        Returns
        -------
        response: requests.Response
            Result of an API call.
        """
        data = json.dumps({"enabled": enabled})
        return _post(
            self._system_private_endpoint("consensus_enabled"), data=data, headers={"content-type": "application/json"}
        )

    def get_consensus_interaction(self) -> requests.Response:
        """
        Performs a GET request to the '{system_base_path}/consensus_enabled' to get boolean value that states
        if the node participates in consensus.

        Example:

        >>> client.get_consensus_interaction().json()
        True

        Returns
        -------
        response: requests.Response
            Result of an API call.
        """
        return _get(self._system_private_endpoint("consensus_enabled"))

    def get_network_info(self) -> requests.Response:
        """
        Performs a GET request to the '{system_base_path}/network'
        to get info about the serialization protocol and the services functioning in the network.

        Example:

        >>> network_info = client.get_network_info().json()
        >>> print(json.dumps(network_info, indent=2))
        {
          "core_version": "0.10.2"
        }

        Returns
        -------
        response: requests.Response
            Result of an API call.
        """
        return _get(self._system_private_endpoint("network"))

    def shutdown(self) -> requests.Response:
        """
        Performs a POST request to the '{system_base_path}/shutdown' to stop the node.
        After receiving this request, the node stops processing transactions, participating in consensus and
        terminates after all messages in the event queue are processed.

        Returns
        -------
        response: requests.Response
            Result of an API call.
        """
        data = json.dumps(None)
        return _post(self._system_private_endpoint("shutdown"), data=data, headers={"content-type": "application/json"})

    # Implementation of ProtobufProviderInterface:
    def _get_proto_sources(self, params: Optional[Dict[str, str]] = None) -> List[ProtoFile]:
        proto_sources_endpoint = _RUST_RUNTIME_URL.format(
            self.schema, self.hostname, self.public_api_port, "proto-sources"
        )
        response = _get(proto_sources_endpoint, params=params)
        if response.status_code != 200 or "application/json" not in response.headers["content-type"]:
            logger.critical(
                "Unsuccessfully attempted to retrieve Protobuf sources.\n" "Status code: %s,\n" "body:\n%s",
                response.status_code,
                response.content,
            )
            raise RuntimeError("Unsuccessfully attempted to retrieve Protobuf sources: {!r}".format(response.content))
        logger.debug("Protobuf sources retrieved successfully.")

        proto_files = [
            ProtoFile(name=proto_file["name"], content=proto_file["content"]) for proto_file in response.json()
        ]

        return proto_files

    def get_main_proto_sources(self) -> List[ProtoFile]:
        # Performs a GET request to the `proto-sources` Exonum endpoint:
        params = {"type": "core"}
        return self._get_proto_sources(params)

    def get_proto_sources_for_artifact(
        self, runtime_id: int, artifact_name: str, artifact_version: str
    ) -> List[ProtoFile]:
        # Raise an exception if runtime ID is not equal to the rust runtime ID
        if runtime_id != RUST_RUNTIME_ID:
            err_msg = f"Provided runtime ID: {runtime_id} is not equal to Rust runtime ID: {RUST_RUNTIME_ID}."
            logger.critical(err_msg)
            raise RuntimeError(err_msg)
        # Performs a GET request to the `proto-sources` Exonum endpoint with a provided artifact name:
        params = {"type": "artifact", "name": artifact_name, "version": artifact_version}

        return self._get_proto_sources(params)

    def _system_public_endpoint(self, endpoint: str) -> str:
        return _SYSTEM_URL.format(self.schema, self.hostname, self.public_api_port, endpoint)

    def _system_private_endpoint(self, endpoint: str) -> str:
        return _SYSTEM_URL.format(self.schema, self.hostname, self.private_api_port, endpoint)


def _get(url: str, params: Optional[Dict[Any, Any]] = None) -> requests.Response:
    # Internal wrapper over requests.get:
    return requests.get(url, params=params)


def _post(url: str, data: str, headers: Dict[str, str]) -> requests.Response:
    # Internal wrapper over requests.post:
    return requests.post(url, data=data, headers=headers)
