# Exonum Python Light Client

[![Travis Build Status](https://travis-ci.com/exonum/python-client.svg?token=DyxSqsiCaQvPg4SYLXqu&branch=master)](https://travis-ci.com/exonum/python-client)

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
| 0.3          | 0.12.1+                 |
| master       | dynamic_services branch |

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
git clone git@github.com:exonum/python-client.git
pip3 install -e python-client
```

### Exonum Client Initialization

```python
from exonum import ExonumClient, MessageGenerator, ModuleManager, gen_keypair

client = ExonumClient(hostname="localhost", public_api_port=8080, private_api_port=8081, ssl=False)
```

### Compiling Proto Files

To compile proto files into the Python analogues we need a protobuf provider and protobuf loader.

Protobuf provider objects accept either file system paths or github public pages.

```python
from exonum.protobuf_provider import ProtobufProvider

main_sources_url = "https://github.com/exonum/exonum/tree/v0.12/exonum/src/proto/schema/exonum"
cryptocurrency_sources_url = (
    "https://github.com/exonum/exonum/tree/v0.12/examples/cryptocurrency-advanced/backend/src/proto"
)
protobuf_provider = ProtobufProvider()
protobuf_provider.add_source(main_sources_url)
protobuf_provider.add_source(cryptocurrency_sources_url, "cryptocurrency-advanced")
```

After creating a protobuf provider, you need to set it for the client.

```python
client.set_protobuf_provider(protobuf_provider)
```

Now you're ready to use protobuf loader:

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
loader.load_service_proto_files(0, service_name="cryptocurrency-advanced")  # Same for specific service.
```

- first argument for `load_service_proto_files` should always be 0.

### Creating Transaction Messages

The following example shows how to create a transaction message.

```python
alice_keys = gen_keypair()

cryptocurrency_service_name = "cryptocurrency-advanced"
loader.load_service_proto_files(0, cryptocurrency_service_name)

cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, "cryptocurrency")

cryptocurrency_message_generator = MessageGenerator(128, cryptocurrency_service_name, "cryptocurrency")

create_wallet_alice = cryptocurrency_module.CreateWallet()
create_wallet_alice.name = 'Alice'

create_wallet_alice_tx = cryptocurrency_message_generator.create_message(create_wallet_alice)
create_wallet_alice_tx.sign(alice_keys)
```

- 128 - service ID.
- key_pair - public and private keys of the ed25519 public-key signature
system.
- "cryptocurrency" means "cryptocurrency.proto" file.

After invoking the sign method, we get a signed transaction.
This transaction is ready for sending to the Exonum node.

### Sending Transaction to the Exonum Node

```python
response = client.send_transaction(signed_message)
```

After successfully sending the message, we'll get a response which will
contain a hash of the transaction. The response looks as follows:

```json
{
    "tx_hash": "3541201bb7f367b802d089d8765cc7de3b7dfc253b12330b8974268572c54c01"
}
```

### Subscribing to events

If you want to subscribe to events, use the following code:

```python
with client.create_subscriber() as subscriber:
    subscriber.wait_for_new_block()
    subscriber.wait_for_new_block()
```

Context manager will automatically create a connection and will disconnect after use.
Or you can manually do the same:

```python
subscriber = client.create_subscriber()
subscriber.connect()
# ... Your code
subscriber.stop()
```

Keep in mind that if you forget to stop the subscriber, you may discover HTTP
errors when you try to use Exonum API.

### More Examples

To see more examples and find out how to work with proofs see the scripts
at the [examples](examples) section.

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

- Websocket cannot be open with the node running through `run-dev`.

For nodes running in `run-dev` mode CORS configuration doesn't allow websocket connect, so attempt to use `Subscriber` will fail.

This behavior is fixed in versions above 12.1.

## License

Apache 2.0 - see [LICENSE](LICENSE) for more information.

[exonum]: https://github.com/exonum/exonum
[protoc]: https://developers.google.com/protocol-buffers/docs/reference/python-generated
