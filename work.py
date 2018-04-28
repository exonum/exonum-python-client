from uuid import uuid4

import exonum.transactions as tx
import exonum.datatypes as exonum

from pysodium import crypto_sign_keypair, crypto_sign_detached, crypto_hash_sha256

from importlib import reload

reload(exonum)
reload(tx)

transactions = tx.transactions(service_id=666)


@transactions
class Test(metaclass=exonum.EncodingStruct):
    x = exonum.Uuid
    y = exonum.u64

public_key, secret_key = crypto_sign_keypair()
a = Test(x=uuid4(), y=12345890)
a.tx(secret_key)
