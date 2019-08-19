import os
from threading import Thread
from websocket import WebSocket
import requests

from .protobuf_loader import ProtobufLoader

BLOCK_URL = "{}://{}:{}/api/explorer/v1/block?height={}"
BLOCKS_URL = "{}://{}:{}/api/explorer/v1/blocks"
SERVICE_URL = "{}://{}:{}/api/services/{}/"
SYSTEM_URL = "{}://{}:{}/api/system/v1/{}"
TX_URL = "{}://{}:{}/api/explorer/v1/transactions"
WEBSOCKET_URI = "ws://{}:{}/api/explorer/v1/blocks/subscribe"


class Subscriber(object):
    def __init__(self, address, port):
        self.address = WEBSOCKET_URI.format(address, port)
        self.is_running = False
        self.handler = None
        self.thread = Thread(target=self._event_processing)
        self.ws_client = WebSocket()
        self.connected = False

    def __enter__(self):
        self.connect()

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def connect(self):
        self.ws_client.connect(self.address)
        self.connected = True

    def set_handler(self, handler):
        self.handler = handler

    def run(self):
        try:
            self.is_running = True
            self.thread.setDaemon(True)
            self.thread.start()
        except RuntimeError as e:
            print(e)

    def _event_processing(self):
        while self.is_running:
            data = self.ws_client.recv()
            if data and self.handler:
                self.handler(data)

    def wait_for_new_block(self):
        if self.is_running:
            print("Subscriber is already running...")
        else:
            self.ws_client.recv()

    def stop(self):
        if self.connected:
            self.ws_client.close()
            self.connected = False

        if self.is_running:
            if self.thread.isAlive():
                self.thread.join()
            self.is_running = False


class ExonumClient(object):
    def __init__(
            self, hostname, public_api_port=80, private_api_port=81, ssl=False
    ):
        # TODO add a warning that object should be created via "with".
        self.schema = "https" if ssl else "http"
        self.hostname = hostname
        self.public_api_port = public_api_port
        self.private_api_port = private_api_port
        self.tx_url = TX_URL.format(self.schema, hostname, public_api_port)

    def _get_main_proto_sources(self):
        return get(
            SYSTEM_URL.format(
                self.schema, self.hostname, self.public_api_port, "proto-sources"
            )
        )

    def _get_proto_sources_for_service(self, runtime_id, service_name):
        params = {
            'artifact': '{}:{}'.format(runtime_id, service_name)
        }
        return get(
            SYSTEM_URL.format(
                self.schema, self.hostname, self.public_api_port, "proto-sources"
            ), params=params
        )

    def protobuf_loader(self):
        return ProtobufLoader(self)

    def available_services(self):
        return get(
            SYSTEM_URL.format(
                self.schema, self.hostname, self.public_api_port, "services"
            )
        )

    """Send transaction into Exonum node via REST IPI.
        msg - A prepared message
    """

    def send_transaction(self, tx):
        try:
            response = requests.post(
                self.tx_url,
                data=tx.to_json(),
                headers={"content-type": "application/json"},
            )
            return response
        except Exception as e:
            return {"error": str(e)}

    def send_transactions(self, txs):
        return [self.send_transaction(tx) for tx in txs]

    def get_block(self, height):
        return get(
            BLOCK_URL.format(self.schema, self.hostname, self.public_api_port, height)
        )

    def get_blocks(
            self, count, latest=None, skip_empty_blocks=False, add_blocks_time=False
    ):
        blocks_url = BLOCKS_URL.format(self.schema, self.hostname, self.public_api_port)
        params = dict()
        params["count"] = count

        if latest:
            params["latest"] = latest
        if skip_empty_blocks:
            params["skip_empty_blocks"] = "true"
        if add_blocks_time:
            params["add_blocks_time"] = "true"

        return get(blocks_url, params=params)

    def get_tx_info(self, tx_hash):
        return get(
            TX_URL.format(self.schema, self.hostname, self.public_api_port)
            + "?hash="
            + tx_hash
        )

    def service_endpoint(self, service_name, sub_uri, private=False):
        port = self.public_api_port if not private else self.private_api_port

        service_url = SERVICE_URL.format(
            self.schema, self.hostname, port, service_name
        )

        return service_url + sub_uri

    def get_service(self, service_name, sub_uri, private=False):
        return get(self.service_endpoint(service_name, sub_uri, private))

    def health_info(self):
        return get(
            SYSTEM_URL.format(
                self.schema, self.hostname, self.public_api_port, "healthcheck"
            )
        )

    def mempool(self):
        return get(
            SYSTEM_URL.format(
                self.schema, self.hostname, self.public_api_port, "mempool"
            )
        )

    def user_agent(self):
        return get(
            SYSTEM_URL.format(
                self.schema, self.hostname, self.public_api_port, "user_agent"
            )
        )

    def create_subscriber(self):
        subscriber = Subscriber(self.hostname, self.public_api_port)
        return subscriber


def get(url, params=None):
    global body
    try:
        return requests.get(url, params=params)
    except requests.exceptions.ConnectionError as e:
        raise e
