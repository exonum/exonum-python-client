from typing import Optional, Callable, Dict, Any
import json
from google.protobuf import json_format

from exonum.module_manager import ModuleManager
from .map_proof import MapProof
from .errors import MapProofBuilderError


class MapProofBuilder:
    def __init__(self):
        self._map_proof = None
        self._key_encoder = None
        self._value_encoder = None

    def _get_encoder(
        self,
        structure_name: str,
        main_module: Optional[str] = None,
        service_name: Optional[str] = None,
        service_module: Optional[str] = None
    ):
        try:
            if main_module:
                module = ModuleManager.import_main_module(main_module)
            elif service_name and service_module:
                module = ModuleManager.import_service_module(service_name, service_module)
            else:
                raise MapProofBuilderError("Module data not provided")

            return getattr(module, structure_name)
        except (ModuleNotFoundError, ImportError):
            error_data = {
                "main_module": main_module,
                "service_name": service_name,
                "service_module": service_module
            }

            raise MapProofBuilderError("Incorrect module data", error_data)
        except AttributeError:
            error_data = {"service_name": structure_name}
            raise MapProofBuilderError("Incorrect structure name", error_data)

    def set_key_encoder(
        self,
        structure_name: str,
        main_module: Optional[str] = None,
        service_name: Optional[str] = None,
        service_module: Optional[str] = None
    ) -> 'MapProofBuilder':
        self._key_encoder = self._get_encoder(structure_name, main_module, service_name, service_module)
        return self

    def set_value_encoder(
        self,
        structure_name: str,
        main_module: Optional[str] = None,
        service_name: Optional[str] = None,
        service_module: Optional[str] = None
    ) -> 'MapProofBuilder':
        self._value_encoder = self._get_encoder(structure_name, main_module, service_name, service_module)

        return self

    def parse_proof(self, proof: Dict[Any, Any]) -> MapProof:
        def build_encoder_function(encoder_class: type) -> Callable[[Dict[Any, Any]], bytes]:
            def func(data: Dict[Any, Any]):
                data_json = json.dumps(data)
                protobuf_obj = encoder_class()
                return json_format.Parse(data_json, protobuf_obj, True).SerializeToString()
            return func

        if not self._key_encoder or not self._value_encoder:
            raise MapProofBuilderError("Encoders aren't set")

        key_encoder_func = build_encoder_function(self._key_encoder)
        value_encoder_func = build_encoder_function(self._value_encoder)

        return MapProof.parse(proof, key_encoder_func, value_encoder_func)
