import json
import os
import requests
import re
import tempfile
import shutil
import sys
from websocket import WebSocket
from threading import Thread

from .protoc import Protoc

BLOCK_URL = "{}://{}:{}/api/explorer/v1/block?height={}"
BLOCKS_URL = "{}://{}:{}/api/explorer/v1/blocks"
SERVICE_URL = "{}://{}:{}/api/services/{}/v1/"
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
        self.protoc = Protoc()

    def __enter__(self):
        self.initialize()
        
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.deinitialize()

    def initialize(self):
        # Create directory for temporary files.
        self.proto_dir = tempfile.mkdtemp(prefix='exonum_client_')

        # Create folder for python files output.
        python_modules_path = os.path.join(self.proto_dir, 'exonum_modules')
        os.makedirs(python_modules_path)

        # Create __init__ file in the exonum_modules directory.
        init_file_path = os.path.join(python_modules_path, '__init__.py')
        open(init_file_path, 'a').close()

        # Add directory with exonum_modules into python path.
        sys.path.append(self.proto_dir)


    def deinitialize(self):
        # Remove generated temporary directory.
        sys.path.remove(self.proto_dir)
        shutil.rmtree(self.proto_dir)

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
        with open(path, "wt") as file_out:
            file_out.write(file_content)

    def _save_files(self, path, files):
        os.makedirs(path)
        for proto_file in files:
            file_name = proto_file['name']
            file_content = proto_file['content']
            file_path = os.path.join(path, file_name)
            self._save_proto_file(file_path, file_content)

    def load_main_proto_files(self):
        # TODO error handling
        proto_contents = self._get_main_proto_sources().json()

        # Save proto_sources in proto/main directory.
        main_dir = os.path.join(self.proto_dir, 'proto', 'main')
        self._save_files(main_dir, proto_contents)

        # Call protoc to compile proto sources.
        proto_dir = os.path.join(self.proto_dir, 'exonum_modules', 'main')
        self.protoc.compile(main_dir, proto_dir)

    def load_service_proto_files(self, runtime_id, service_name):
        # TODO error handling
        proto_contents = self._get_proto_sources_for_service(runtime_id, service_name).json()

        # Save proto_sources in proto/service_name directory.
        service_module_name = re.sub(r'[-. :/]', '_', service_name)
        service_dir = os.path.join(self.proto_dir, 'proto', service_module_name)
        self._save_files(service_dir, proto_contents)

        # Call protoc to compile proto sources.
        main_dir = os.path.join(self.proto_dir, 'proto', 'main')
        proto_dir = os.path.join(self.proto_dir, 'exonum_modules', service_module_name)
        self.protoc.compile(service_dir, proto_dir, include=main_dir)

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

    def system_endpoint(self, service_name, sub_uri, private=False):
        port = self.public_api_port if not private else self.private_api_port

        service_url = SERVICE_URL.format(
            self.schema, self.hostname, port, service_name
        )

        return service_url + sub_uri

    def get_service(self, service_name, sub_uri, private=False):
        return get(self.system_endpoint(service_name, sub_uri, private))

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
