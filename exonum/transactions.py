from codecs import encode
from struct import pack
from os import urandom
from pysodium import crypto_sign_keypair, crypto_sign_detached, crypto_hash_sha256
import inspect

MESSAGE_CLASS = 0
MESSAGE_TYPE = 0

def linenumber_of_member(proto_module, m):
    proto_source = inspect.getsource(proto_module)
    pos = proto_source.find("name='{}'".format(m))
    assert pos != -1
    return pos

class MsgIndex:
    messages = {}
    def __init__(self, messages):
        for pos, proto_type in enumerate(messages) :
            self.messages[proto_type[1]] = int(pos)

    def id(self, msg):
        pos = self.messages.get(type(msg))
        assert pos is not None
        return pos


class ExonumClient:
    def __init__(self, proto_module, service_id):
        self.service_id = service_id

        messages = []
        for name, obj in inspect.getmembers(proto_module):
            if inspect.isclass(obj):
                messages.append((name, obj))
        messages.sort(key=lambda x: linenumber_of_member(proto_module, x[0]))
        self.messages = MsgIndex(messages)

    def new_tx(self, tx_message, public_key, secret_key):
        msg_buffer = {
            'author': public_key,
            'message_class': pack("<B", MESSAGE_CLASS),
            'message_type': pack("<B", MESSAGE_TYPE),
            'message_id': pack("<H", self.messages.id(tx_message)),
            'service_id': pack("<H", self.service_id),
            'body': b''.join([tx_message.SerializeToString()])
        }

        full_data = b''.join([public_key,                   # author
                              pack("<B", MESSAGE_CLASS),    # message_class
                              pack("<B", MESSAGE_TYPE),     # message_type
                              pack("<H", self.service_id),  # service_id
                              pack("<H", self.messages.id(tx_message)),    # message_id
                              b''.join([tx_message.SerializeToString()])]) # body

        signature = self.gen_signature(full_data, secret_key)
        data = b''.join([full_data, signature])
        signed_tx_body =  encode(data, 'hex').decode("utf-8")

        params = {
            "tx_body": signed_tx_body,
        }
        return params

    def gen_keypair(self):
        return crypto_sign_keypair()

    def gen_hash(self):
        return crypto_hash_sha256(urandom(256))

    def gen_signature(self, data, secret_key):
        return crypto_sign_detached(data, secret_key)

