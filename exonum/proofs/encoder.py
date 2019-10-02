"""Tools for Creating Value Binary Encoders."""
from typing import Callable, Dict, Any
import json

import base64
import copy

from google.protobuf import json_format


# TODO This custom is required because of a bug in the Python Protobuf implementation:
# https://github.com/protocolbuffers/protobuf/issues/6602
# This workaround is sort of a kludge, and it may lead to an incorrect behavior for int8/uint8 arrays.
# But currently Exonum does not have them, so it seems OK. When the issue is fixed,
# this code will be removed.
def _encode_byte_lists_to_base64(obj: Dict[Any, Any]) -> Dict[Any, Any]:
    def _visit(entries: Dict[Any, Any]) -> None:
        for key, value in entries.items():
            if isinstance(value, dict):
                _visit(value)
            elif isinstance(value, list) and all(map(lambda x: 0 <= x <= 255, value)):
                obj_raw = bytes(value)
                entries[key] = str(base64.b64encode(obj_raw), "utf-8")

    obj_copy = copy.deepcopy(obj)

    _visit(obj_copy)

    return obj_copy


def build_encoder_function(encoder_class: type) -> Callable[[Dict[Any, Any]], bytes]:
    """
    With this function you can create an encoder function for a value.

    It creates a Protobuf converter from a value (as a dict) to bytes which can be used either
    in MapProof or in ListProof.

    Parameters
    ----------
    encoder_class: type
        Class of the Protobuf message that will be used to convert data to bytes.

    Returns
    ------
    Callable[[Dict[Any, Any]], bytes]
        A converter function from a value to bytes.
    """

    def func(data: Dict[Any, Any]) -> bytes:
        # TODO temporary workaround for the problem described above.
        preencoded_data = _encode_byte_lists_to_base64(data)

        data_json = json.dumps(preencoded_data)
        protobuf_obj = encoder_class()

        return json_format.Parse(data_json, protobuf_obj, True).SerializeToString()

    return func
