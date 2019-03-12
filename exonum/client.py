import json
import requests

BLOCK_URL = "{}://{}:{}/api/explorer/v1/block?height={}"
BLOCKS_URL = "{}://{}:{}/api/explorer/v1/blocks"
SERVICE_URL = "{}://{}:{}/api/services/{}/v1/"
SYSTEM_URL = "{}://{}:{}/api/system/v1/{}"
TX_URL = "{}://{}:{}/api/explorer/v1/transactions"


class ExonumClient(object):
    def __init__(self, service_name, hostname, public_api_port=80, private_api_port=81, ssl=False):
        self.schema = "https" if ssl else "http"
        self.hostname = hostname
        self.public_api_port = public_api_port
        self.private_api_port = private_api_port
        self.service_name = service_name
        self.tx_url = TX_URL.format(self.schema, hostname, public_api_port)
        self.service_url = SERVICE_URL.format(self.schema, hostname, public_api_port, service_name)

    """Send transaction into Exonum node via REST IPI. 
        msg - A prepared message
    """
    def send_transaction(self, msg):
        try:
            response = requests.post(self.tx_url, data=msg.to_json(), headers={"content-type": "application/json"})
            return response.text
        except Exception as e:
            return {"error": str(e)}

    def get_block(self, height):
        return get(BLOCK_URL.format(self.schema, self.hostname, self.public_api_port, height))

    def get_blocks(self, count=None, latest=None, skip_empty_blocks=False, add_blocks_time=False):
        pass

    def get_tx_info(self, tx_hash):
        return get(TX_URL.format(self.schema, self.hostname, self.public_api_port) + "?hash=" + tx_hash)

    def get_service(self, sub_uri):
        return get(self.service_url + sub_uri)

    def health_info(self):
        return get(SYSTEM_URL.format(self.schema, self.hostname, self.public_api_port, "healthcheck"))

    def mempool(self):
        return get(SYSTEM_URL.format(self.schema, self.hostname, self.public_api_port, "mempool"))

    def user_agent(self):
        return get(SYSTEM_URL.format(self.schema, self.hostname, self.public_api_port, "user_agent"))


def get(url):
    global body
    try:
        response = requests.get(url)
        body = response.json()
    except Exception as e:
        body = {"error": str(e)}
    finally:
        return json.dumps(body, indent=4)
