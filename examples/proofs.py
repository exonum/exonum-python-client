"""Example of Obtaining and Verifying Proofs."""

from typing import Dict, Any
from exonum import ExonumClient, MessageGenerator, ModuleManager
from exonum.crypto import Hash
from exonum.proofs import (
    ListProof,
    MapProof,
    MapProofBuilder,
    MalformedMapProofError,
    build_encoder_function,
    ListProofVerificationError,
    MalformedListProofError,
)
from examples.transactions import (
    RUST_RUNTIME_ID,
    CRYPTOCURRENCY_ARTIFACT_NAME,
    CRYPTOCURRENCY_INSTANCE_NAME,
    create_wallet,
    get_cryptocurrency_instance_id,
    ensure_status_code,
)


def run() -> None:
    """This example creates a wallet in the Cryptocurrency service, retrieves
    proofs for the wallet and verifies them.
    For the example to work, be sure to have `exonum-cryptocurrency-advanced`
    service instance with name `XNM` deployed."""
    client = ExonumClient(hostname="127.0.0.1", public_api_port=8080, private_api_port=8081)

    with client.protobuf_loader() as loader:
        # Load and compile proto files:
        loader.load_main_proto_files()
        loader.load_service_proto_files(RUST_RUNTIME_ID, CRYPTOCURRENCY_ARTIFACT_NAME)

        instance_id = get_cryptocurrency_instance_id(client)

        cryptocurrency_message_generator = MessageGenerator(instance_id, CRYPTOCURRENCY_ARTIFACT_NAME)

        alice_keypair = create_wallet(client, cryptocurrency_message_generator, "Alice")

        wallet_info_response = client.get_service(
            CRYPTOCURRENCY_INSTANCE_NAME, "v1/wallets/info?pub_key={}".format(alice_keypair.public_key.hex())
        )
        ensure_status_code(wallet_info_response)
        wallet_info = wallet_info_response.json()

        # A map proof to the whole Exonum state hash:
        proof_to_table = wallet_info["wallet_proof"]["to_table"]
        # Expected hash of the proof to the table is a state hash of the block:
        expected_to_table_hash_raw = wallet_info["block_proof"]["block"]["state_hash"]
        expected_to_table_hash = Hash(bytes.fromhex(expected_to_table_hash_raw))

        # Verify the proof to the table:
        verify_proof_to_table(proof_to_table, expected_to_table_hash)

        # A map proof to the wallet as a part of the Cryptocurrency schema:
        proof_to_wallet = wallet_info["wallet_proof"]["to_wallet"]
        # Expected hash of the proof to the wallet is the value stored in the
        # proof to the table:
        expected_to_wallet_hash_raw = wallet_info["wallet_proof"]["to_table"]["entries"][0]["value"]
        expected_to_wallet_hash = Hash(bytes.fromhex(expected_to_wallet_hash_raw))

        # Verify the proof to the wallet:
        verify_proof_to_wallet(proof_to_wallet, expected_to_wallet_hash)

        # Map the proof for the transactions associtated with the wallet:
        proof_wallet_history = wallet_info["wallet_history"]["proof"]
        # Expected hash for the wallet history is the hash stored in the proof
        # to the wallet:
        expected_history_hash_raw = wallet_info["wallet_proof"]["to_wallet"]["entries"][0]["value"]["history_hash"]
        expected_history_hash = Hash(bytes(expected_history_hash_raw["data"]))

        # Verify the proof for the wallet history:
        verify_wallet_history_proof(proof_wallet_history, expected_history_hash)


def verify_proof_to_table(proof: Dict[Any, Any], expected_hash: Hash) -> None:
    """Verifies MapProof to table."""

    # Keys in the proof to the table are encoded as a byte sequence (tag,
    # group_id, index_id):
    def key_encoder(data: Dict[str, int]) -> bytes:
        import struct

        format_str = ">HIH"
        res = struct.pack(format_str, data["tag"], data["group_id"], data["index_id"])
        return res

    # Values in the proof to the table are encoded as a byte sequence parsed
    # from a hexadecimal string:
    def value_encoder(data: str) -> bytes:
        return bytes.fromhex(data)

    try:
        parsed_proof = MapProof.parse(proof, key_encoder, value_encoder)

        result = parsed_proof.check()

        if result.root_hash() == expected_hash:
            print("MapProof to table verified successfully")
        else:
            print("MapProof to table verification failed")
    except MalformedMapProofError:
        print("Received malformed proof to the table")


def verify_proof_to_wallet(proof: Dict[Any, Any], expected_hash: Hash) -> None:
    """Verifies MapProof to table."""

    # Keys in the proof to the wallet are encoded as a byte sequence parsed from
    # a hexadecimal string:
    def key_encoder(data: str) -> bytes:
        return bytes.fromhex(data)

    # Values in the proof to the wallet are encoded as a Protobuf binary
    # representation of the `Wallet` structure:
    cryptocurrency_module = ModuleManager.import_service_module(CRYPTOCURRENCY_ARTIFACT_NAME, "service")
    value_encoder = build_encoder_function(cryptocurrency_module.Wallet)

    try:
        parsed_proof = MapProof.parse(proof, key_encoder, value_encoder)

        result = parsed_proof.check()

        if result.root_hash() == expected_hash:
            print("MapProof to wallet verified successfully")
        else:
            print("MapProof to wallet verification failed")
    except MalformedMapProofError:
        print("Received malformed proof to the wallet")


def verify_wallet_history_proof(proof: Dict[Any, Any], expected_hash: Hash) -> None:
    """Verifies ListProof for the wallet history."""

    # To convert a value to bytes we can use `bytes.fromhex` since values are
    # hexadecimal strings:
    try:
        parsed_proof = ListProof.parse(proof, value_to_bytes=bytes.fromhex)
        parsed_proof.validate(expected_hash)

        print("ListProof for the wallet history verified successfully")
    except ListProofVerificationError:
        print("ListProof for the wallet history verification failed")
    except MalformedListProofError:
        print("Received malformed proof for the wallet history")


if __name__ == "__main__":
    run()
