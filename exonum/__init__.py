"""
Exonum Python Light Client.

This library is designed to provide useful interfaces for Exonum blockchain.

The main modules you can be interested in:
  - client:
    Module with ExonumClient, the main entity to interact with Exonum. It will
    provide you with the methods to work with API, send transactions, etc.
  - message:
    Module with classes to generate transactions.
  - module_manager:
    This module contains ModuleManager entity to work with generated Protobuf classes
    (see [documentation](https://exonum.com/doc/version/latest/architecture/transactions/#serialization)
    if you are not familiar with the Exonum Protobuf workflow).
  - proofs:
    Module with ListProof and MapProof classes which can be used to verify proofs obtained from Exonum.
"""

from .client import ExonumClient
from .message import MessageGenerator, ExonumMessage
from .module_manager import ModuleManager
from .proofs import ListProof
