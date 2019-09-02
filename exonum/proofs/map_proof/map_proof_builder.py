from typing import Optional, Callable, Dict, Any
import json
from google.protobuf import json_format

from exonum.module_manager import ModuleManager
from .map_proof import MapProof
from .errors import MapProofBuilderError


class MapProofBuilder:
    """
    Builder for a MapProof.

    This class is capable of creating a MapProof from the Dict[Any, Any].
    Since MapProof converts both keys and values to bytes for hashing, this
    class generates a converter functions from the relevant protobuf structures.

    Designed workflow example:

    ```python
    proof_builder = MapProofBuilder()
    proof_builder.set_key_encoder('BitVec', main_module='helpers')
    proof_builder.set_value_encoder('Wallet', service_name='cryptocurrency', service_module='service')
    proof = proof_builder.build_proof(map_proof)
    ```

    If your key/value type should not be converted to bytes through protobuf, use `MapProof.parse`
    instead and provide your converter functions by yourself.

    If one of the types should be converted manually, but the other one should use protobuf, you can
    use `build_encoder_function` method which takes a protobuf message class as an argument and
    returns a converter function.
    """

    def __init__(self):
        """ Constructor of the MapProofBuilder. """
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
        """
        Method to set the key encoder.

        If the protobuf structure for the key lies in the main module, you should
        provide `main_module` argument.
        Otherwise, you should provide both `service_name` and `service_module`.

        Parameters
        ----------
        structure_name: str
            Name of the protobuf structure to be used in converted function.
        main_module: Optional[str]
            Name of the main module
        service_name: Optional[str]
            Name of the service.
        service_module: Optional[str]
            Name of the service module.

        Raises
        ------
        MapProofBuilderError
            If provided data was incorrect, this exception will be rised.
        """
        self._key_encoder = self._get_encoder(structure_name, main_module, service_name, service_module)
        return self

    def set_value_encoder(
        self,
        structure_name: str,
        main_module: Optional[str] = None,
        service_name: Optional[str] = None,
        service_module: Optional[str] = None
    ) -> 'MapProofBuilder':
        """
        Method to set the value encoder.

        If the protobuf structure for the value lies in the main module, you should
        provide `main_module` argument.
        Otherwise, you should provide both `service_name` and `service_module`.

        Parameters
        ----------
        structure_name: str
            Name of the protobuf structure to be used in converted function.
        main_module: Optional[str]
            Name of the main module
        service_name: Optional[str]
            Name of the service.
        service_module: Optional[str]
            Name of the service module.

        Raises
        ------
        MapProofBuilderError
            If provided data was incorrect, this exception will be rised.
        """
        self._value_encoder = self._get_encoder(structure_name, main_module, service_name, service_module)

        return self

    @staticmethod
    def build_encoder_function(encoder_class: type) -> Callable[[Dict[Any, Any]], bytes]:
        """
        Static method to create encoder function.

        Normally you won't use this function, but if you need to use MapProof with one custom
        converter function and one protobuf-based, you can create protobuf converter with this
        method.

        Parameters
        ----------
        encoder_class: type
            Class of the protobuf message that will be used to convert data to bytes.

        Returns
        ------
        Callable[[Dict[Any, Any]], bytes]
            A converter function for the MapProof.
        """
        def func(data: Dict[Any, Any]):
            data_json = json.dumps(data)
            protobuf_obj = encoder_class()
            return json_format.Parse(data_json, protobuf_obj, True).SerializeToString()
        return func

    def build_proof(self, proof: Dict[Any, Any]) -> MapProof:
        """
        Method to build the MapProof from the Dict[Any, Any].

        This method should be called only after `set_key_encoder` and `set_value_encoder`.

        Parameters
        ----------
        proof: Dict[Any, Any]
            Raw ProofMap that will be parsed.

        Raises
        ------
        MapProofBuilderError
            If method is called without prior `set_key_encoder` and `set_value_encoder` calls,
            this exception will be rised.

        MalformedMapProofError
            If the provided raw MapProof was malformed and parsing failed, this exception will
            be rised.
        """
        if not self._key_encoder or not self._value_encoder:
            raise MapProofBuilderError("Encoders aren't set")

        key_encoder_func = self.build_encoder_function(self._key_encoder)
        value_encoder_func = self.build_encoder_function(self._value_encoder)

        return MapProof.parse(proof, key_encoder_func, value_encoder_func)
