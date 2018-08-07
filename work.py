import json
import exonum.transactions as tx
import exonum.datatypes as exonum

from uuid import uuid4
from pysodium import crypto_sign_keypair

from importlib import reload

reload(exonum)
reload(tx)

transactions = tx.transactions(service_id=521)


# @transactions
# class Test(metaclass=exonum.EncodingStruct):
#     x = exonum.Uuid
#     y = exonum.u64


# public_key, secret_key = crypto_sign_keypair()
# a = Test(x=uuid4(), y=12345890)
# a.tx(secret_key)

public_key = bytes.fromhex(
    "0f17189c062e7f3fbb47a21834d41e4d5c5388dd7db38c4de1ce732971a38ef9"
)
secret_key = bytes.fromhex(
    "5520c351b7760aedeef32687918eb2587ab515e4ae0eeef271a0f0a99f1df3710f17189c062e7f3fbb47a21834d41e4d5c5388dd7db38c4de1ce732971a38ef9"
)


@transactions
class CreateUser(metaclass=exonum.EncodingStruct):
    public_key = exonum.PublicKey()
    name = exonum.Str()


a = CreateUser(public_key=public_key, name="Me")

print(json.dumps(a.tx(secret_key), indent=2))
print("tx hash:", a.hash(secret_key))
