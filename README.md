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

| Light Client | Exonum |
|--------------|--------|
| 0.1          | 0.9.*  |
| 0.2          | 0.10.* |

## System Dependencies

- Python 3.5 or above.
- Package installer for Python3 (pip3) 

## Examples

The following example shows how to create an instance of the Exonum client
which will be able to work with Exonum node with
cryptocurrency service, at http://localhost:8080
address:

### Installing Python Light Client

First of all we need to install our client library:

```shell
git clone git@github.com:exonum/python-client.git
pip3 -e install python-client
```

### Getting Source Files of the Exonum Framework

```shell
git clone https://github.com/exonum/exonum.git
```

### Compiling Proto Files

To compile proto files into the Python analogues we need to run the
following command:

```shell
python3 -m exonum -e exonum -s exonum/examples/cryptocurrency/src/proto -o client-example/proto
```
- exonum - path to the source files of the Exonum framework.
- exonum/examples/cryptocurrency/src/proto - path to service's proto files.
- client-example/proto - path where the proto files should be compiled.

### Exonum Client Initialization
```python
import proto.cryptocurrency_pb2
from exonum.client import ExonumClient
from exonum.message import MessageGenerator, gen_keypair

client = ExonumClient("cryptocurrency", "localhost", 8080, 8081, False)
```
- "cryptocurrency" - service name.
- "localhost" - host to communicate with.
- 8080 - listen port of the public API. Default value is: 80.
- 8081 - listen port of the private API. Default value is: 81.
- False - defines if SSL connection should be used. Default value is: False.

### Creating Transaction Messages
The following example shows how to create a transaction message.

```python
msg_generator = MessageGenerator(proto.cryptocurrency_pb2, 128)
tx_message = msg_generator.create_message("CreateWallet", name="Alice")
key_pair = gen_keypair()
signed_message = tx_message.sign(key_pair)
```

- proto.cryptocurrency_pb2 - module with classes compiled from the proto
files.
- 128 - service ID.
- "CreateWallet" - name of the message.
- key_pair - public and private keys of the ed25519 public-key signature 
system.

After invoking sign method we get a signed transaction. 
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

## License
Apache 2.0 - see [LICENSE](LICENSE) for more information.

[exonum]: https://github.com/exonum/exonum
[protoc]: https://developers.google.com/protocol-buffers/docs/reference/python-generated
