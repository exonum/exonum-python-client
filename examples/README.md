# Examples for the Exonum Python Light Client

In this folder you can find sample script to understand how to work with the
Exonum Python Light Client.

Recommended order is the following:

- [api.py](api.py): Minimal example demonstrating how to initialize the client
  and retrieve some information via REST API.
- [protobuf.py](protobuf.py): Example of downloading and compiling Protobuf
  sources received from the Exonum node.
- [deploy.py](deploy.py): Sample script that deploys an artifact and starts a
  service instance.
- [transactions.py](transactions.py): Sample script that uses the deployed and
  started cryptocurrency service to run several transactions.
- [proofs.py](proofs.py): Sample script that retrieves MapProofs and ListProof
  for a wallet from the Cryptocurrency service and verifies them.

All the examples expect an Exonum node to be running on the localhost with
public port 8080 and private port 8081.

All examples except for the `api.py` and `protobuf.py` also expect the node to
have an `exonum-cryptocurrency-advanced` artifact available for deploy.

## How to run examples

First of all, ensure that you have both `exonum-cryptocurrency-advanced` and
`exonum-python-client` installed:

```sh
# Run the following in the exonum core folder.
cargo install --path examples/cryptocurrency-advanced/backend --force
# Run the following in the exonum-python-client folder.
pip install -e . --no-binary=protobuf
```

Then, run the `exonum-cryptocurrency-advanced` example in the `run-dev` mode:

```sh
exonum-cryptocurrency-advanced run-dev -p /tmp/crypt
```

`/tmp/crypt` is a folder for temporary config and data files created 
by the `exonum-cryptocurrency-advanced` process.

You may optionally run with `--clean` option as well, if this is not the first launch.

Then, you can run any example:

```sh
python examples/api.py
python examples/deploy.py
python examples/transactions.py
```
