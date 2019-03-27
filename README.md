# Exonum Python Light Client

Python client for [Exonum Framework][exonum].

## Overview

Exonum light client is Python library for working with Exonum blockchain 
from the client side and can be easily integrated to an existing 
application. Also, Exonum light client provides access to common utils 
toolkit which contains some helpful functions for hashing, cryptography,
serialization etc.

## Capabilities
By using the client you are able to perform the following operations:

- Submit transactions to the node
- Receive transaction information 
- Receive blockchain blocks information 
- Receive node system information 
- Receive node status information  

## Compatibility
The following table shows versions compatibility:  

| Light Client | Exonum |
|--------------|--------|
| 0.1          | 0.9.*  |
| 0.2          | 0.10.* |

## System dependencies

- Python 3.5 or above.
- Package installer for Python3 (pip3) 

## Examples

The following example shows how to create the instance of exonum client
which will be able to work with Exonum node which includes 
cryptocurrency service, at `http://localhost:8080` 
address:

### Installation Python Light Client

First of all we need to install our client:

```shell
git clone git@github.com:exonum/python-client.git
pip3 -e install python-client
```

### Getting source files of Exonum framework

```shell
git clone https://github.com/exonum/exonum.git
```

### Compiling proto files

To compile proto files into python analogue we need to run such command:

```shell
python3 -m exonum -e exonum -s exonum/examples/cryptocurrency/src/proto -o client-example/proto
```
- exonum - path to source files of exonum framework.
- exonum/examples/cryptocurrency/src/proto - path to service's proto files.
- client-example/proto - path where proto files should be compiled.

### Exonum Client Initialization
```python
import proto.cryptocurrency_pb2
from exonum.client import ExonumClient
from exonum.message import MessageGenerator, gen_keypair, encode

client = ExonumClient("cryptocurrency", "localhost", 8080, 8081, False)
```
- "cryptocurrency" - service name.
- "localhost" - host to communicate with.
- 8080 - listen port of public api. Default value is: 80.
- 8081 - listen port of private api. Default value is: 81.
- False - defines if using ssl connection. Default value is: False.

### Creating Transaction Messages
The following example shows how to create the transaction message.

```python
msg_generator = MessageGenerator(proto.cryptocurrency_pb2, 128)
tx_message = msg_generator.create_message("CreateWallet", name="Alice")
key_pair = gen_kaypair()
signed_message = tx_message.sign(key_pair)
```

- proto.cryptocurrency_pb2 - module with classes which compiled from
proto files. 
- 128 - service id.
- "CreateWallet" - name of the message.
- key_pair - public and private keys of ed25519 public-key signature 
system.

After invoking `sign` method we get a signed transaction which is 
ready to be sending into Exonum node.

### Sending a transaction into the Exonum node

```python
response = client.send_transaction(signed_message)
```

After successful sending a message we'll get a response which will be 
contains a hash of the transaction and will be looking something like 
this:
 
```json
{
    "tx_hash": "3541201bb7f367b802d089d8765cc7de3b7dfc253b12330b8974268572c54c01"
}
```

## License
Apache 2.0 - see [LICENSE](LICENSE) for more information.

[exonum]: https://github.com/exonum/exonum
[protoc]: https://developers.google.com/protocol-buffers/docs/reference/python-generated