# Examples for the Exonum Python Light Client

In this folder you can find sample script to understand how to work with the
Exonum Python Light Client.

Recommended order is the following:

- [api.py](api.py): Minimal example demonstrating how to initialize the client
  and retrieve some information via REST API.
- [protobuf.py](protobuf.py): Example of downloading and compiling Protobuf
  sources from the Exonum.
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
