# Exonum Python Light Client

[![Travis Build Status](https://travis-ci.com/exonum/exonum-python-client.svg?branch=master)](https://travis-ci.com/exonum/exonum-python-client)
[![codecov](https://codecov.io/gh/exonum/exonum-python-client/branch/master/graph/badge.svg)](https://codecov.io/gh/exonum/exonum-python-client)

Python client for the [Exonum Framework][exonum].

## Overview

Exonum Light Client is a Python library for working with Exonum blockchain
from the client side. It can be easily integrated to an existing
application. Also, Exonum Light Client provides access to common utils
toolkit which contains some helpful functions for hashing, cryptography,
serialization, etc.

## Capabilities

By using the client you are able to perform the following operations:

- Submit transactions to the node
- Receive information on transactions
- Receive information on blockchain blocks
- Receive information on the node system
- Receive information on the node status

## Compatibility

The following table shows versions compatibility:  

| Light Client | Exonum                  |
|--------------|-------------------------|
| 0.1          | 0.9.*                   |
| 0.2          | 0.10.*                  |
| 0.3.1        | 0.12.*                  |
| 1.0.x        | 1.0.*                   |
| master       | `exonum` master branch  |

## System Dependencies

- Python 3.5 or above.
- Package installer for Python3 (pip3)

## Examples

The following example shows how to create an instance of the Exonum client
which will be able to work with an Exonum node with the
Cryptocurrency Advanced service mounted on it, at `http://localhost:8080`
address:

### Installing Python Light Client

First of all we need to install our client library:

```shell
git clone git@github.com:exonum/exonum-python-client.git
pip3 install -e exonum-python-client --no-binary=protobuf
```

### Exonum Client Initialization

```python
from exonum_client import ExonumClient, ModuleManager, MessageGenerator
from exonum_client.crypto import KeyPair

client = ExonumClient(hostname="localhost", public_api_port=8080, private_api_port=8081, ssl=False)
```

### Compiling Proto Files

To compile proto files into the Python analogues we need a protobuf loader:

```python
with client.protobuf_loader() as loader:
    #  Your code goes here.
```

Since loader acquires resources on initialization, creating via context manager is recommended.
Otherwise you should initialize and deinitialize client manually:

```python
loader = client.protobuf_loader()
loader.initialize()
# ... Some usage
loader.deinitialize()
```

Then we need to run the following code:

```python
loader.load_main_proto_files()  # Load and compile main proto files, such as `runtime.proto`, `consensus.proto`, etc.
loader.load_service_proto_files(runtime_id=0, service_name='exonum-supervisor:1.0.0')  # Same for specific service.
```

- runtime_id=0 here means, that service works in Rust runtime.

### Creating Transaction Messages

The following example shows how to create a transaction message:

```python
alice_keys = KeyPair.generate()

cryptocurrency_artifact_name = "exonum-cryptocurrency-advanced"
cryptocurrency_artifact_version = "1.0.0"
loader.load_service_proto_files(
    runtime_id=0, 
    artifact_name=cryptocurrency_artifact_name, 
    artifact_version=cryptocurrency_artifact_version
)

cryptocurrency_module = ModuleManager.import_service_module(
    cryptocurrency_artifact_name, cryptocurrency_artifact_version, "service"
)

cryptocurrency_message_generator = MessageGenerator(
    instance_id=1024, 
    artifact_name=cryptocurrency_artifact_name, 
    artifact_version=cryptocurrency_artifact_version
)

create_wallet_alice = cryptocurrency_module.CreateWallet()
create_wallet_alice.name = 'Alice'

create_wallet_alice_tx = cryptocurrency_message_generator.create_message(create_wallet_alice)
create_wallet_alice_tx.sign(alice_keys)
```

- 1024 - service instance ID.
- alice_keys - public and private keys of the ed25519 public-key signature
system.

After invoking the sign method, we get a signed transaction.
This transaction is ready for sending to the Exonum node.

### Sending Transaction to the Exonum Node

After successfully sending the message, we'll get a response which will
contain a hash of the transaction:

```python
response = client.public_api.send_transaction(create_wallet_alice_tx)
```

```json
{
    "tx_hash": "3541201bb7f367b802d089d8765cc7de3b7dfc253b12330b8974268572c54c01"
}
```

### Subscribing to events

If you want to subscribe to events (subscription_type: "transactions" or "blocks"), use the following code:

```python
with client.create_subscriber(subscription_type="blocks") as subscriber:
    subscriber.wait_for_new_event()
    subscriber.wait_for_new_event()
```

Context manager will automatically create a connection and will disconnect after use.
Or you can manually do the same:

```python
subscriber = client.create_subscriber(subscription_type="blocks")
subscriber.connect()
# ... Your code
subscriber.stop()
```

Keep in mind that if you forget to stop the subscriber, you may discover HTTP
errors when you try to use Exonum API.

### Getting Data on the Available Services

```python
client.public_api.available_services().json()
```

The code will show a list of the artifacts available for the start and a list of
working services:

```python
{
  "artifacts": [
    {
      "runtime_id": 0,
      "name": "exonum-supervisor",
      "version": "1.0.0"
    },
    {
      "runtime_id": 0,
      "name": "exonum-explorer-service",
      "version": "1.0.0"
    }
  ],
  "services": [
    {
      "spec": {
        "id": 2,
        "name": "explorer",
        "artifact": {
          "runtime_id": 0,
          "name": "exonum-explorer-service",
          "version": "1.0.0"
        }
      },
      "status": "Active",
      "pending_status": null
    },
    {
      "spec": {
        "id": 0,
        "name": "supervisor",
        "artifact": {
          "runtime_id": 0,
          "name": "exonum-supervisor",
          "version": "1.0.0"
        }
      },
      "status": "Active",
      "pending_status": null
    }
  ]
}
```

### More Examples

To see more examples and find out how to work with proofs go [here][proof].

Also you can find the sample scripts at the [examples](examples) section.

### Testing

To run tests, use the following command:

```sh
python3 -m unittest
```

### Contributing

You can see notes for developers in the [Contribution Guide](CONTRIBUTING.md)
page.

### Known Problems

If within use you discover the following error:

```sh
TypeError: Couldn't build proto file into descriptor pool!
```

It is due to the issue with Protobuf binary wheels. The only work around is to
install the pure Python implementation.

```sh
pip uninstall protobuf
pip install --no-binary=protobuf protobuf
```

## License

Apache 2.0 - see [LICENSE](LICENSE) for more information.

[exonum]: https://github.com/exonum/exonum
[protoc]: https://developers.google.com/protocol-buffers/docs/reference/python-generated
[proof]: PROOF.md
