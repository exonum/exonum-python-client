import random

random.seed(0)


EXONUM_PROTO = "http"
EXONUM_IP = "127.0.0.1"
EXONUM_PUBLIC_PORT = "8080"
EXONUM_PRIVATE_PORT = "8081"
EXONUM_URL_BASE = "{}://{}:{}/"

SYSTEM_ENDPOINT_POSTFIX = "api/system/v1/{}"
SERVICE_ENDPOINT_POSTFIX = "api/services/{}/{}"
EXPLORER_ENDPOINT_POSTFIX = "api/explorer/v1/{}"


def random_alphanumeric_string(length=32):
    import string

    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def proto_sources_response(service):
    from requests.models import Response

    with open("tests/api_responses/proto_sources_{}.json".format(service)) as file:
        content = file.read()

        response = Response()
        response.code = "OK"
        response.status_code = 200
        response.headers = {"content-type": "application/json; charset=utf8"}
        response._content = bytes(content, "utf-8")

        return response


def mock_response(status_code, content=None):
    import json
    from requests.models import Response
    from requests.status_codes import _codes as status_codes

    response = Response()
    response.code = status_codes[status_code][0]
    response.status_code = status_code
    if content:
        response.headers = {"content-type": "application/json; charset=utf8"}
        content = json.dumps(content)
        response._content = bytes(content, "utf-8")

    return response


def mock_requests_get(cls_obj, url, params=None):
    exonum_public_base = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PUBLIC_PORT)
    _exonum_private_base = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PRIVATE_PORT)

    proto_sources_endpoint = exonum_public_base + "api/runtimes/rust/proto-sources"

    # public
    healthcheck_endpoint = exonum_public_base + SYSTEM_ENDPOINT_POSTFIX.format("healthcheck")
    stats_endpoint = exonum_public_base + SYSTEM_ENDPOINT_POSTFIX.format("stats")
    user_agent_endpoint = exonum_public_base + SYSTEM_ENDPOINT_POSTFIX.format("user_agent")
    # private
    peers_endpoint = _exonum_private_base + SYSTEM_ENDPOINT_POSTFIX.format("peers")
    consensus_endpoint = _exonum_private_base + SYSTEM_ENDPOINT_POSTFIX.format("consensus_enabled")
    network_endpoint = _exonum_private_base + SYSTEM_ENDPOINT_POSTFIX.format("network")

    block_endpoint = exonum_public_base + EXPLORER_ENDPOINT_POSTFIX.format("block")
    blocks_endpoint = exonum_public_base + EXPLORER_ENDPOINT_POSTFIX.format("blocks")
    transactions_endpoint = exonum_public_base + EXPLORER_ENDPOINT_POSTFIX.format("transactions")

    responses = {
        # Proto sources endpoints.
        # Proto sources without params (main sources):
        (proto_sources_endpoint, "{'type': 'core'}"): proto_sources_response("main"),
        # Proto sources for the supervisor service:
        (
            proto_sources_endpoint,
            "{'type': 'artifact', 'name': 'exonum-supervisor', 'version': '0.11.0'}",
        ): proto_sources_response("supervisor"),
        # System endpoints:
        # public
        (healthcheck_endpoint, "None"): mock_response(200),
        (stats_endpoint, "None"): mock_response(200),
        (user_agent_endpoint, "None"): mock_response(200),
        # private
        (peers_endpoint, "None"): mock_response(200),
        (consensus_endpoint, "None"): mock_response(200),
        (network_endpoint, "None"): mock_response(200),
    }

    # Explorer endpoints
    if url == block_endpoint:
        content = None
        status_code = 200

        if not isinstance(params["height"], int) or params["height"] < 0:
            status_code = 400
        else:
            content = {"height": params["height"]}

        responses.update({(block_endpoint, str(params)): mock_response(status_code, content)})
    if url == blocks_endpoint:
        content = None
        status_code = 200

        if not isinstance(params["count"], int) or params["count"] < 0:
            status_code = 400
        elif "earliest" in params and "latest" in params and params["latest"] - params["earliest"] < 0:
            status_code = 200

        responses.update({(blocks_endpoint, str(params)): mock_response(status_code, content)})
    if url == transactions_endpoint:
        content = None
        status_code = 200

        if not isinstance(params["hash"], str) or not params["hash"].isalnum():
            status_code = 400

        responses.update({(transactions_endpoint, str(params)): mock_response(status_code, content)})

    return responses[(url, str(params))]


def mock_requests_post(cls_obj, url, data=None, headers=None):
    exonum_public_base = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PUBLIC_PORT)
    _exonum_private_base = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PRIVATE_PORT)

    endpoints = {
        "transactions_endpoint": exonum_public_base + EXPLORER_ENDPOINT_POSTFIX.format("transactions"),
        "shutdown_endpoint": _exonum_private_base + SYSTEM_ENDPOINT_POSTFIX.format("shutdown"),
        "consensus_endpoint": _exonum_private_base + SYSTEM_ENDPOINT_POSTFIX.format("consensus_enabled"),
        "peers_endpoint": _exonum_private_base + SYSTEM_ENDPOINT_POSTFIX.format("peers"),
    }

    if url in endpoints.values():
        return mock_response(200)
