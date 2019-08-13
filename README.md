# Exonum Python Light Client

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
pip3 -e install python-client
```

### Exonum Client Initialization
```python
import proto.cryptocurrency_pb2
from exonum import ExonumClient, MessageGenerator, ModuleManager, gen_keypair

with ExonumClient(hostname="localhost", public_api_port=8080, private_api_port=8081, ssl=False) as client:
    ...
```

Since client acquires resources on initialization, create Client via context manager is recommended.
Otherwise you should initialize and deinitialize client manually:

```python
client = ExonumClient(hostname="localhost", public_api_port=8080, private_api_port=8081, ssl=False)
client.initialize()
# ... Some usage
client.deinitialize()
```

### Compiling Proto Files

To compile proto files into the Python analogues we need to run the
following code:

```python
client.load_main_proto_files() # Load and compile main proto files, such as `runtime.proto`, `consensus.proto`, etc.
client.load_service_proto_files(runtime_id=0, service_name='exonum-supervisor:0.11.0') # Same for specific service.
```

- runtime_id=0 here means, that service works in Rust runtime.

### Creating Transaction Messages
The following example shows how to create a transaction message.

```python
keys = gen_keypair()

cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'
client.load_service_proto_files(runtime_id=0, cryptocurrency_service_name)

cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')

cryptocurrency_message_generator = MessageGenerator(service_id=1024, service_name=cryptocurrency_service_name)

create_wallet_alice = cryptocurrency_module.CreateWallet()
create_wallet_alice.name = 'Alice'

create_wallet_alice_tx = cryptocurrency_message_generator.create_message('CreateWallet', create_wallet_alice)
create_wallet_alice_tx.sign(keys)
```

- 1024 - service instance ID.
- "CreateWallet" - name of the message.
- key_pair - public and private keys of the ed25519 public-key signature 
system.

After invoking sign method we get a signed transaction. 
This transaction is ready for sending to the Exonum node.

### Getting data on availiable services

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

### Testing

To run tests, use the following command:
```sh
python3 -m unittest
```

## License
Apache 2.0 - see [LICENSE](LICENSE) for more information.

[exonum]: https://github.com/exonum/exonum
[protoc]: https://developers.google.com/protocol-buffers/docs/reference/python-generated
