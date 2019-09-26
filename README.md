# Exonum Python Light Client

[![Travis Build Status](https://travis-ci.com/exonum/python-client.svg?token=DyxSqsiCaQvPg4SYLXqu&branch=master)](https://travis-ci.com/exonum/python-client)

Python client for [Exonum Framework][exonum].

## Overview

Exonum light client is a Python library for working with Exonum blockchain 
from the client side. It can be easily integrated to an existing 
application. Also, Exonum light client provides access to common utils 
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
| master       | dynamic_services branch |

## System Dependencies

- Python 3.5 or above.
- Package installer for Python3 (pip3) 

## Examples

The following example shows how to create an instance of the Exonum client
which will be able to work with Exonum node with
cryptocurrency-advanced service, at http://localhost:8080
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

To compile proto files into the Python analogues we need a protobuf loader.

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
loader.load_service_proto_files(runtime_id=0, service_name='exonum-supervisor:0.12.0')  # Same for specific service.
```

- runtime_id=0 here means, that service works in Rust runtime.

### Creating Transaction Messages
The following example shows how to create a transaction message.

```python
alice_keys = gen_keypair()

cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'
loader.load_service_proto_files(runtime_id=0, cryptocurrency_service_name)

cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')

cryptocurrency_message_generator = MessageGenerator(service_id=1024, service_name=cryptocurrency_service_name)

create_wallet_alice = cryptocurrency_module.CreateWallet()
create_wallet_alice.name = 'Alice'

create_wallet_alice_tx = cryptocurrency_message_generator.create_message('CreateWallet', create_wallet_alice)
create_wallet_alice_tx.sign(alice_keys)
```

- 1024 - service instance ID.
- "CreateWallet" - name of the message.
- key_pair - public and private keys of the ed25519 public-key signature 
system.

After invoking sign method we get a signed transaction. 
This transaction is ready for sending to the Exonum node.

To see more examples and find out how to work with proofs go [here][proof].

### Getting Data on the Available Services

```python
client.available_services().json()
```

It will show list of artifacts available to start, and list of working services.
Format of the output:
```python
{
  'artifacts': [
    {
      'runtime_id': 0,
      'name': 'exonum-cryptocurrency-advanced:0.11.0'
    },
    {
      'runtime_id': 0,
      'name': 'exonum-supervisor:0.11.0'
    }
  ],
  'services': [
    {
      'id': 1024,
      'name': 'XNM',
      'artifact': {
        'runtime_id': 0,
        'name': 'exonum-cryptocurrency-advanced:0.11.0'
      }
    },
    {
      'id': 0,
      'name': 'supervisor',
      'artifact': {
        'runtime_id': 0,
        'name': 'exonum-supervisor:0.11.0'
      }
    }
  ]
}
```

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

Keep in mind that if you'll forget to stop subscriber, you may discover HTTP errors when you'll try to use Exonum API.

### Testing

To run tests, use the following command:
```sh
python3 -m unittest
```

### Known problems

If within use you discover a following error:
```sh
TypeError: Couldn't build proto file into descriptor pool!
```

It's because of the issue with protobuf binary wheels. The only work around it to install the pure python implementation.

```sh
pip uninstall protobuf
pip install --no-binary=protobuf protobuf
```

## License
Apache 2.0 - see [LICENSE](LICENSE) for more information.

[exonum]: https://github.com/exonum/exonum
[protoc]: https://developers.google.com/protocol-buffers/docs/reference/python-generated
[proof]: PROOF.MD
