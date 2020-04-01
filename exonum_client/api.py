"""
Exonum API Module.

This module provides several API classes:
  - Api: a class with basic REST functionality.
  - PublicApi: a subclass of class Api that provides methods to interact with public API of an Exonum node.
  - PrivateApi: a subclass of class Api that provides methods to interact with private API of an Exonum node.
  - ServiceApi: a class that provides methods to interact with node services.
"""
from typing import Optional, Any, Union, List, Dict, Iterable

import json
from logging import getLogger
import requests

from .message import ExonumMessage

# pylint: disable=C0103
logger = getLogger(__name__)


class Api:
    """Api class provides basic REST functionality."""

    # constants
    RUST_RUNTIME_ID = 0

    def __init__(self, hostname: str, port: int, schema: str):
        """
        Constructor of Api.

        Parameters
        ----------
        hostname: str
            Examples: '127.0.0.1', 'www.some_node.com'.
        port: int
            API port of an Exonum node.
        schema: str
             Communication protocol: 'https' or 'http'.
        """
        self.schema = schema
        self.hostname = hostname
        self.port = port
        # Example of a formatted prefix: "https://127.0.0.1:8000"
        self.endpoint_prefix = "{}://{}:{}/api".format(self.schema, hostname, port)

    @staticmethod
    def get(url: str, params: Optional[Dict[Any, Any]] = None) -> requests.Response:
        """Internal wrapper over requests.get"""
        return requests.get(url, params=params)

    @staticmethod
    def post(url: str, data: str, headers: Dict[str, str]) -> requests.Response:
        """Internal wrapper over requests.post"""
        return requests.post(url, data=data, headers=headers)


class PublicApi(Api):
    """PublicApi class provides methods to interact with the public API of an Exonum node."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self._tx_url = self.endpoint_prefix + "/explorer/v1/transactions"
        self._block_url = self.endpoint_prefix + "/explorer/v1/block"
        self._blocks_url = self.endpoint_prefix + "/explorer/v1/blocks"
        self._services_url = self.endpoint_prefix + "/services/supervisor/services"

    def get_block(self, height: int) -> requests.Response:
        """
        Gets a block at the provided height.

        Example:

        >>> public_api = PublicApi("127.0.0.1", 80, "http")
        >>> block = public_api.get_block(2).json()
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
        return self.get(self._block_url, params={"height": height})

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

        return self.get(self._blocks_url, params=params)

    def get_tx_info(self, tx_hash: str) -> requests.Response:
        """
        Gets information about the transaction with the provided hash.

        Example:

        >>> public_api = PublicApi("127.0.0.1", 80, "http")
        >>> tx_info = public_api.get_tx_info(tx_hash).json()
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
        return self.get(self._tx_url, params={"hash": tx_hash})

    def available_services(self) -> requests.Response:
        """
        Gets a list of available services from Exonum.

        Example:

        >>> public_api = PublicApi("127.0.0.1", 80, "http")
        >>> available_services = public_api.available_services().json()
        >>> print(json.dumps(available_services, indent=2))
        {
          "artifacts": [
            {
              "runtime_id": 0,
              "name": "exonum-supervisor",
              "version": "1.0.0-rc.1"
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
                  "version": "1.0.0-rc.1"
                }
              },
              "status": "active"
            }
          ]
        }
        """
        return self.get(self._services_url)

    def get_instance_id_by_name(self, name: str) -> Optional[int]:
        """
        Gets an ID of the service instance with the provided name.

        Example:

        >>> public_api = PublicApi("127.0.0.1", 80, "http")
        >>> id = public_api.get_instance_id_by_name("cryptocurrency")
        >>> id
        42

        Parameters
        ----------
        name: Name of the service.

        Returns
        -------
        result: Optional[int]
            ID of the instance (int) if the instance with given name exists, otherwise None is returned.

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

        >>> public_api = PublicApi("127.0.0.1", 80, "http")
        >>> response = public_api.send_transaction(message)
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
        response = self.post(self._tx_url, data=message.pack_into_json(), headers={"content-type": "application/json"})
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


class PrivateApi(Api):
    """PrivateApi class provides methods to interact with the private API of an Exonum node."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self._system_url = self.endpoint_prefix + "/system/v1/{}"

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
        response = self.post(self._system_url.format("peers"), data=data, headers={"content-type": "application/json"})
        return response

    def get_info(self) -> requests.Response:
        """
        Performs a GET request to the '{system_base_path}/info' to get info about a node. The info includes:
         - consensus status;
         - list of connected peers;
         - exonum version;
         - rust compiler version;
         - info about OS;

        Example:

        >>> private_api = PrivateApi("127.0.0.1", 81, "http")
        >>> peers = private_api.get_info().json()
        >>> print(json.dumps(peers, indent=4))
        {
            "consensus_status": "active",
            "connected_peers": [
                {
                  "address": "127.0.0.1:54610",
                  "public_key": "5211b00d4e84e7a523d3377a72bd9be42bac14cab9e0c412f8e8a165947dbe9b",
                  "direction": "incoming"
                },
                {
                  "address": "127.0.0.1:54617",
                  "public_key": "1ffd9a18dd2949b874e1cd850193f80fe1cd7023dd20f76348a56da3c5732cf4",
                  "direction": "incoming"
                },
                {
                  "address": "127.0.0.1:54613",
                  "public_key": "8b91b55d88902c1e91d4acfd374684c07d7878fb3bfc4a04851fed36b8381dca",
                  "direction": "incoming"
                }
            ],
            "exonum_version": "1.0.0-rc.1",
            "rust_version": "1.41.0",
            "os_info": "Mac OS (10.15.3) (unknown)"
        }

        Returns
        -------
        response: requests.Response
            Result of an API call.
            If it is successful, a list of peers will be returned.
        """
        return self.get(self._system_url.format("info"))

    def set_consensus_interaction(self, enabled: bool = True) -> requests.Response:
        """
        Performs a POST request to the '{system_base_path}/consensus_status'
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
        return self.post(
            self._system_url.format("consensus_status"), data=data, headers={"content-type": "application/json"}
        )

    def get_stats(self) -> requests.Response:
        """
        Performs a GET request to the '{system_base_path}/stats'
        to get the node's statistic. The statistic includes:
         - current height of the blockchain;
         - amount of transactions in the transaction pool;
         - amount of committed transactions;
         - amount of transactions in the cache;
         - work duration of the node in seconds.

        Example:

        >>> private_api = PrivateApi("127.0.0.1", 81, "http")
        >>> network_info = private_api.get_stats().json()
        >>> print(json.dumps(network_info, indent=2))
        {
          "height": 63,
          "tx_pool_size": 3
          "tx_count": 10,
          "tx_cache_size": 5,
          "uptime": 487
        }

        Returns
        -------
        response: requests.Response
            Result of an API call.
        """
        return self.get(self._system_url.format("stats"))

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
        return self.post(self._system_url.format("shutdown"), data=data, headers={"content-type": "application/json"})


class ServiceApi(Api):
    """ServiceApi class provides methods to interact with service API."""

    def __init__(self, service_name: str, *args: Any, **kwargs: Any):
        """
        Constructor of ServiceApi.

        Parameters
        ----------
        service_name: str
            Name of a service.
        *args, **kwargs:
            Arguments for Api class constructor.
        """
        super().__init__(*args, **kwargs)

        self._api_url = f"{self.schema}://{self.hostname}:{self.port}/api/services/{service_name}/"

    def service_endpoint(self, sub_uri: str) -> str:
        """
        Creates a service endpoint for a given sub-uri.

        Example:

        >>> service_api = ServiceApi("supervisor", "127.0.0.1", "8080", "http")
        >>> service_api.service_endpoint("deploy-artifact")
        http://127.0.0.1:8081/api/services/supervisor/deploy-artifact

        Parameters
        ----------
        sub_uri: str
            Additional part of a URL to be added to the endpoint, e.g. "some/sub/uri?parameter=value"
        private: bool
            Denotes if a private port should be used. Defaults to False.

        Returns
        -------
        url: str
            Returns a service REST API URL based on the provided parameters.
        """
        return self._api_url + sub_uri

    def get_service(self, sub_uri: str) -> requests.Response:
        """
        Performs a GET request to the endpoint generated by the `service_endpoint` method.

        Parameters are the same as in `service_endpoint`.

        Returns
        -------
        response: requests.Response
            Result of an API call.
        """
        return self.get(self.service_endpoint(sub_uri))

    def post_service(self, sub_uri: str, data: Any, data_format: str = "json") -> requests.Response:
        """
        Performs a POST request to the endpoint generated by the `service_endpoint` method.

        Parameters are the same as in `service_endpoint` except for `data`.
        `data` is expected to be serialized in JSON value or in protobuf binary format.

        `format` allows to specify in which type of format the data is represented.

        Returns
        -------
        response: requests.Response
            Result of an API call.
        """
        if data_format == "json":
            headers = {"content-type": "application/json"}
        else:
            headers = {"content-type": "application/octet-stream"}

        return self.post(self.service_endpoint(sub_uri), data=data, headers=headers)
