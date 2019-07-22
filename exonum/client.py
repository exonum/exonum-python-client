import json
import os
import requests
from websocket import WebSocket
from threading import Thread

BLOCK_URL = "{}://{}:{}/api/explorer/v1/block?height={}"
BLOCKS_URL = "{}://{}:{}/api/explorer/v1/blocks"
SERVICE_URL = "{}://{}:{}/api/services/{}/v1/"
SYSTEM_URL = "{}://{}:{}/api/system/v1/{}"
TX_URL = "{}://{}:{}/api/explorer/v1/transactions"
WEBSOCKET_URI = "ws://{}:{}/api/explorer/v1/blocks/subscribe"

def find_protoc():
    if PROTOC_ENV_NAME in os.environ:
        return os.getenv(PROTOC_ENV_NAME)
    else:
        return shutil.which("protoc")

class Subscriber(object):
    def __init__(self, address, port):
        self.address = WEBSOCKET_URI.format(address, port)
        self.is_running = False
        self.handler = None
        self.thread = Thread(target=self._event_processing)
        self.ws_client = WebSocket()

    def connect(self):
        self.ws_client.connect(self.address)

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
        if not self.is_running:
            return
        self.is_running = False
        if self.thread.isAlive():
            self.thread.join()
        self.ws_client.close()


class ExonumClient(object):
    def __init__(
        self, service_name, hostname, public_api_port=80, private_api_port=81, ssl=False, proto_dir='proto'
    ):
        self.schema = "https" if ssl else "http"
        self.hostname = hostname
        self.public_api_port = public_api_port
        self.private_api_port = private_api_port
        self.service_name = service_name
        self.tx_url = TX_URL.format(self.schema, hostname, public_api_port)
        self.service_url = SERVICE_URL.format(
            self.schema, hostname, public_api_port, service_name
        )
        self.proto_dir = proto_dir

        if not os.path.exists(self.proto_dir):
            os.makedirs(self.proto_dir)

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

    def _save_proto_file(self, path, file_content):
        os.mkdir(path)
        with open(path, "wt") as file_out:
            file_out.write(file_content)

    def _save_files(self, path, files):
        for proto_file in files:
            file_name = proto_file['name']
            file_content = proto_file['content']
            file_path = os.path.join(path, file_name)
            self._save_proto_file(file_path, file_content)

    def load_main_proto_files(self):
        proto_contents = self._get_main_proto_sources()

        # Save proto_sources in proto/main directory
        main_dir = os.path.join(self.proto_dir, 'proto', 'main')
        self._save_files(main_dir, proto_contents)

        # TODO call protoc to compile proto sources

    def load_service_proto_files(self, runtime_id, service_name):
        proto_contents = self._get_proto_sources_for_service(runtime_id, service_name)

        # Save proto_sources in proto/service_name directory
        service_dir = os.path.join(self.proto_dir, 'proto', 'service_name')
        self._save_files(service_dir, proto_contents)

        # TODO call protoc to compile proto sources

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

    def get_service(self, sub_uri):
        return get(self.service_url + sub_uri)

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
        try:
            subscriber = Subscriber(self.hostname, self.public_api_port)
            subscriber.connect()
            return subscriber
        except Exception as e:
            print(e)

    def _get_services(self):
        return get(
            SYSTEM_URL.format(
                self.schema, self.hostname, self.public_api_port, "services"
            )
        )



def get(url, params=None):
    global body
    try:
        return requests.get(url, params=params)
    except requests.exceptions.ConnectionError as e:
        raise e
