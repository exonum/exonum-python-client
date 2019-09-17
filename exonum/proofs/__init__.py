"""Exonum Proofs module.

This subpackage provides interfaces for parsing and verifying proofs obtained from Exonum.

For list proofs use ListProof class, for map proofs (surprisingly) MapProof and MapProofBuilder classes.

Since keys and values are hashed during proof verification, and the algorigthm of serialization to bytes
may vary for different indices, you will have to provide encoder functions to the Proof object.

If key/value is serialized to bytes using Protobuf, a function 'build_encoder_function' will generate
an encoder function for you."""
from .list_proof import *
from .map_proof import *
from .encoder import build_encoder_function
