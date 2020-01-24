# Examples

All the examples in this file are assuming that `Exonum` node runs with the
`cryptocurrency-advanced` service deployed and started.

## Issue Funds

Create an **Issue** object:

```python
issue_alice = cryptocurrency_module.Issue()  
issue_alice.amount = 50  
issue_alice.seed = random.getrandbits(64)
```

Create an **Issue** message and sign it:

```python
issue_alice_tx = cryptocurrency_message_generator.create_message(issue_alice)
issue_alice_tx.sign(alice_keys)
 ```

- "Issue" - name of the message

Send a transaction:

```python
client.public_api.send_transaction(issue_alice_tx)
```

Obtain the wallet and check if the balance has been increased:

```python
service_public_api = client.service_public_api(instance_name)
alice_wallet = service_public_api.get_service("v1/wallets/info?pub_key=" + alice_keys.public_key.hex()).json()
```

## Transfer Funds

First of all, we need to create another wallet:

```python
bob_keys = KeyPair.generate() 
create_wallet_bob = cryptocurrency_module.CreateWallet()  
create_wallet_bob.name = 'Bob'

create_wallet_bob_tx = cryptocurrency_message_generator.create_message(create_wallet_bob)  
create_wallet_bob_tx.sign(bob_keys)  
client.public_api.send_transaction(create_wallet_bob_tx)
```

Import the **Types** module:

```python
types_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'types')
```

Create a **Transfer** object:

```python
transfer = cryptocurrency_module.Transfer()  
transfer.amount = 100  
transfer.seed = random.getrandbits(64)
hash_address = message_generator.pk_to_hash_address(bob_keys.public_key)
transfer_message.to.CopyFrom(types_module.Hash(data=hash_address.value))
```

Send a **Transfer** transaction. Use Alice's keys to sign the transaction:

```python
transfer_tx = cryptocurrency_message_generator.create_message(transfer)  
transfer_tx.sign(alice_keys)  
client.public_api.send_transaction(transfer_tx)
```

## Verifying MapProof to a Table

You have to obtain a '**to_table**' JSON structure to verify it further:

```python
to_table = wallet_resp['wallet_proof']['to_table']
```

Example of a **to_table** structure:

```json
    {
        "entries": [{
            "key": {
                "tag": 3,
                "group_id": 1024,
                "index_id": 0
            },
            "value": "54ee97312256f2b32be82d82f409e905ee622ffe37a883adb85df1b17837a01b"
        }],
        "proof": [{
            "path": "0",
            "hash": "447b06d6800f6e69cfd7c8a49a7f8df3d877f22442bb88615d9d74989ff3f2d5"
        }, {
            "path": "1011001101100100010001101010100001110010101101100110111001001101010011011001110101110100000011100000001101010011110000110011001110101111001011001001111111101101011100101010110100011101000110011001100000110111000010100000100111000001000010110101000000001010",
            "hash": "2db14e60ef4eb9a6c4c6df7919843d792bd52c68144a5f143eb70694652864e2"
        }, {
            "path": "1011110000101000001000110111110110110011111111001111101001101111011010100101101100111000010111100110000110100011100100100011001010001111110000101010001101000010100011000011011101110100011100011101111011100001011101011000000010011001101100001000111000000010",
            "hash": "f0483ee2e9816aad9939e9e2be7336d96d6abc1a19e3d59d16a500d1ba9c416f"
        }, {
            "path": "11",
            "hash": "e425bcda782240a2f2545d2daf1a2f5229723b9188723a222748c32ea9e0dd08"
        }]
    }
```

Key and value encoders are required to parse "MapProof to table":

```python
def key_encoder(data):
    import struct
    format_str = '>HIH'

    return struct.pack(format_str, data['tag'], data['group_id'], data['index_id'])


def value_encoder(data):
    return bytes.fromhex(data)
```

Parse the proof and obtain a CheckedMapProof entity:

```python
parsed_proof = MapProof.parse(to_table, key_encoder, value_encoder)
result = parsed_proof.check()
```

Get a root hash and a block state hash:

```python
root_hash = result.root_hash().hex()
state_hash = wallet_resp['block_proof']['block']['state_hash']
```

**Root hash** and **state hash** should be equal:

```python
self.assertEqual(root_hash, state_hash)
```

## Verifying MapProof to a Wallet

You have to obtain a **'to_wallet'** JSON structure to verify it further:

```python
to_wallet = wallet_resp['wallet_proof']['to_wallet']
```

Example of a **to_wallet** structure:

```json
    {
        "entries": [{
            "key": "f8b0150493cbfb42fee98b6ee83c5599a07366dc0a86c9c392668414ad8264bc",
            "value": {
                "pub_key": {
                    "data": [248, 176, 21, 4, 147, 203, 251, 66, 254, 233, 139, 110, 232, 60, 85, 153, 160, 115, 102, 220, 10, 134, 201, 195, 146, 102, 132, 20, 173, 130, 100, 188]
                },
                "name": "Alice",
                "balance": 0,
                "history_len": 2,
                "history_hash": {
                    "data": [184, 117, 111, 23, 88, 139, 217, 47, 85, 201, 248, 182, 26, 171, 59, 208, 164, 13, 173, 67, 207, 17, 236, 207, 250, 97, 79, 189, 13, 211, 164, 244]
                }
            }
        }],
        "proof": [{
            "path": "0011001010100001010101010100000110111000001010100100010010110100110111010111101100011101000100101010011001110001000100011011101100110111001001101011101110001011000000000000000111001000000110110000011011011100111100111011100110110000011111011100001100100110",
            "hash": "9538a91413645f8b15141b8cad77265cae3295ce2702e9407c5cd0f1ccd6de62"
        }]
    }
```

In this case you are able to use an autogenerated value encoder:

```python
cryptocurrency_encoder = build_encoder_function(cryptocurrency_module.Wallet)
```

Parse the proof and obtain a CheckedMapProof entity:

```python
parsed_proof = MapProof.parse(to_wallet, lambda x: bytes.fromhex(x), cryptocurrency_encoder)
result = parsed_proof.check()
```

Get a root hash and a wallet hash:

```python
root_hash = result.root_hash().hex()
wallet_hash = wallet_resp['wallet_proof']['to_table']['entries'][0]['value']
```

**Root hash** and **wallet hash** should be equal:

```python
self.assertEqual(root_hash, wallet_hash)
```

## Verifying ListProof to wallet_history

You have to obtain a JSON structure of the 'wallet_history' proofs to verify it further:

```python
wallet_history = wallet_resp['wallet_history']['proof']
```

Get a history hash:

```python
history_hash_raw = wallet_resp['wallet_proof']['to_wallet']['entries'][0]['value']['history_hash']['data']
history_hash = Hash(bytes(history_hash_raw))
```

Parse ListProof and validate it:

```python
proof = ListProof.parse(wallet_history)
res = proof.validate(history_hash)
```

Example of **res**:

```python
    [(0, '3a0565bdb05967faab6eed6bf994d682a29a1e811fba3481f373d0d4f7e90b22'), (1, '92b33ff4e2ddec0801541a9e20ab4e1132cd17a6b4e2d666368fa9bab0eb6542')]
```

Example of '**wallet_history**':

```json
    {
        "proof": {
            "proof": [],
            "entries": [
                [0, "3a0565bdb05967faab6eed6bf994d682a29a1e811fba3481f373d0d4f7e90b22"],
                [1, "92b33ff4e2ddec0801541a9e20ab4e1132cd17a6b4e2d666368fa9bab0eb6542"]
            ],
            "length": 2
        },
        "transactions": ["0a120a100a05088008100212070a05416c69636512220a20f8b0150493cbfb42fee98b6ee83c5599a07366dc0a86c9c392668414ad8264bc1a420a4031f65704d8e5d7ec40f41dfff7f36f7e0895163c69c462fc0ef1b66e043e308a772f0532fd4666722d5ed0712d83911dd49367b61642d089b0e8b806c5a0ef0e", "0a3a0a380a0308800812310a220a20be5cbc46803d37e3a728300541f1d8cd3b1cc4637776c7183b3e956fffe8c458106418a0fbf88cddf7f6b2880112220a20f8b0150493cbfb42fee98b6ee83c5599a07366dc0a86c9c392668414ad8264bc1a420a40a8d27095e75ad442300e16ca7caf78024a1bce7eabad8785fe2929afdf1b2b154947caa7424e9a95e954de5bf4fbbb165a1a24a637664dd94d289db43264ad0e"]
    }
```

The number of transactions in **res** should be equal to the number of transactions in **wallet_history**.
