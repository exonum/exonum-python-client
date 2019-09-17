# Examples for the Exonum Python light client

In this folder you can find sample script to understand how to work with Exonum Python light client.

Recommended order is the following:

- [api.py](api.py): Minimal example demostrating how to initialize a client and retrieve some information via REST API.
- [protobuf.py](protobuf.py): Example of downloading and compiling protobuf sources from the Exonum.
- [deploy.py](deploy.py): Sample script that deploys an artifact and starts a service instance.
- [transactions.py](transactions.py): Sample script that uses deployed and started cryptocurrency service to
run several transactions.
- [proofs.py](proofs.py): Sample script that retrieves MapProofs and ListProof for wallet from
cryptocurrency service and verifies them.

All the examples expect an Exonum node to be running on the localhost with public port 8080 and private port 8081.

All examples except for the `api.py` and `protobuf.py` also expect node to have an `exonum-cryptocurrency-advanced`
artifact to be available to deploy.
