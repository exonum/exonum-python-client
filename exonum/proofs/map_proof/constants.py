"""Common Constants for the MapProof Module."""
from ..hasher import Hasher

# Size in bytes of Hash. Equal to the hash function output (32):
KEY_SIZE = Hasher.HASH_SIZE
# Size in bytes of ProofPath:
PROOF_PATH_SIZE = KEY_SIZE + 2
