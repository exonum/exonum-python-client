Welcome to the documentation of the Exonum Python Light Client!
===============================================================

========
Overview
========

Exonum Light Client is a Python library for working with Exonum blockchain
from the client side. It can be easily integrated to an existing
application. Also, Exonum Light Client provides access to common utils
toolkit which contains some helpful functions for hashing, cryptography,
serialization, etc.

============
Capabilities
============

By using the client you are able to perform the following operations:

- Submit transactions to the node
- Receive information on transactions
- Receive information on blockchain blocks
- Receive information on the node system
- Receive information on the node status

===================
System Dependencies
===================

- Python 3.5 or above.
- Package installer for Python3 (pip3)

========
Examples
========

The following example shows how to create an instance of the Exonum client
which will be able to work with an Exonum node with the
Cryptocurrency Advanced service mounted on it, at http://localhost:8080
address:

------------------------------
Installing Python Light Client
------------------------------

First of all, we need to install our client library:

::

    git clone git@github.com:exonum/exonum-python-client.git
    pip3 install -e exonum-python-client

----------------------------
Exonum Client Initialization
----------------------------

>>> from exonum_client import ExonumClient, ModuleManager, MessageGenerator
>>> from exonum_client.crypto import KeyPair
>>> client = ExonumClient(hostname="localhost", public_api_port=8080, private_api_port=8081, ssl=False)


---------------------
Compiling Proto Files
---------------------

To compile proto files into the Python analogues we need a Protobuf loader:

>>> with client.protobuf_loader() as loader:
>>>     #  Your code goes here.

Since loader acquires resources on initialization, it is recommended that you
create the loader via the context manager.
Otherwise you should initialize and deinitialize the client manually:

>>> loader = client.protobuf_loader()
>>> loader.initialize()
>>> # ... Some usage
>>> loader.deinitialize()

Then we need to run the following code:

>>> loader.load_main_proto_files()  # Loads and compiles main proto files, such as `runtime.proto`, `consensus.proto`, etc.
>>> loader.load_service_proto_files(runtime_id=0, service_name='exonum-supervisor:0.12.0')  # Same for a specific service.

- runtime_id=0 here means, that service works in Rust runtime.

-----------------------------
Creating Transaction Messages
-----------------------------

The following example shows how to create a transaction message:

>>> alice_keys = KeyPair.generate()
>>>
>>> cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.12.0'
>>> loader.load_service_proto_files(runtime_id=0, service_name=cryptocurrency_service_name)
>>>
>>> cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')
>>> cryptocurrency_message_generator = MessageGenerator(service_id=1024, artifact_name=cryptocurrency_service_name)
>>>
>>> create_wallet_alice = cryptocurrency_module.CreateWallet()
>>> create_wallet_alice.name = 'Alice'
>>> create_wallet_alice_tx = cryptocurrency_message_generator.create_message(create_wallet_alice)
>>> create_wallet_alice_tx.sign(alice_keys)

- 1024 - service instance ID.
- alice_keys - public and private keys of the ed25519 public-key signature system.

After invoking the sign method we get a signed transaction.
This transaction is ready for sending to an Exonum node.

--------------------------------------
Sending Transaction to the Exonum Node
--------------------------------------

After successfully sending the message, we'll get a response which will
contain a hash of the transaction:

>>> response = client.send_transaction(create_wallet_alice_tx)
{
    "tx_hash": "3541201bb7f367b802d089d8765cc7de3b7dfc253b12330b8974268572c54c01"
}

---------------------
Subscribing to events
---------------------

If you want to subscribe to events, use the following code:

>>> with client.create_subscriber() as subscriber:
>>>     subscriber.wait_for_new_block()
>>>     subscriber.wait_for_new_block()

Context manager will automatically create a connection and will disconnect after use.
Or you can manually do the same:

>>> subscriber = client.create_subscriber()
>>> subscriber.connect()
>>> # ... Your code
>>> subscriber.stop()

Keep in mind that if you forget to stop the subscriber, you may discover HTTP
errors when you try to use Exonum API.

--------------------------------------
Getting Data on the Available Services
--------------------------------------

The code below will show a list of the artifacts available for the start and a
list of working services:

>>> client.available_services().json()
{
  'artifacts': [
    {
      'runtime_id': 0,
      'name': 'exonum-cryptocurrency-advanced:0.12.0'
    },
    {
      'runtime_id': 0,
      'name': 'exonum-supervisor:0.12.0'
    }
  ],
  'services': [
    {
      'id': 1024,
      'name': 'XNM',
      'artifact': {
        'runtime_id': 0,
        'name': 'exonum-cryptocurrency-advanced:0.12.0'
      }
    },
    {
      'id': 0,
      'name': 'supervisor',
      'artifact': {
        'runtime_id': 0,
        'name': 'exonum-supervisor:0.12.0'
      }
    }
  ]
}

-------------
More Examples
-------------

You can find the sample scripts in the GitHub repository
`examples <https://github.com/exonum/python-client/examples/>`_ section:

.. toctree::
   :maxdepth: 2
   :caption: Contents:


=====================
Modules Documentation
=====================

Documentation for the modules in the Exonum Python Light Client:

.. toctree::
   :maxdepth: 2
   :caption: API documentation:

   modules

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
