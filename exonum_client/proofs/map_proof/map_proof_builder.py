"""MapProofBuilder module."""
from typing import Optional, Dict, Any
from logging import getLogger

from exonum_client.module_manager import ModuleManager
from .map_proof import MapProof
from .errors import MapProofBuilderError
from ..encoder import build_encoder_function

# pylint: disable=C0103
logger = getLogger(__name__)


class MapProofBuilder:
    """
    Builder for MapProof.

    This class is capable of creating MapProof from Dict[Any, Any].
    Since MapProof converts both keys and values to bytes for hashing, this
    class generates converter functions from the relevant Protobuf structures.

    Designed workflow example:

    >>> proof_builder = MapProofBuilder()
    >>> proof_builder.set_key_encoder('BitVec', main_module='types')
    >>> proof_builder.set_value_encoder('Wallet', service_name='cryptocurrency', service_module='service')
    >>> proof = proof_builder.build_proof(map_proof)

    If your key/value type does not require convertion to bytes through Protobuf, use `MapProof.parse`
    instead and provide your converter functions by yourself.

    If one of the types requires manual convertion, but the other one should use Protobuf, you can
    use `build_encoder_function` function from encoder.py which takes a Protobuf message class as an argument and
    returns a converter function.
    """

    def __init__(self) -> None:
        """ Constructor of MapProofBuilder. """
        self._key_encoder: Optional[type] = None
        self._value_encoder: Optional[type] = None

    @staticmethod
    def _get_encoder(
        structure_name: str,
        main_module: Optional[str] = None,
        service_name: Optional[str] = None,
        service_module: Optional[str] = None,
    ) -> type:
        try:
            if main_module:
                module = ModuleManager.import_main_module(main_module)
            elif service_name and service_module:
                module = ModuleManager.import_service_module(service_name, service_module)
            else:
                err = MapProofBuilderError("Module data not provided")
                logger.warning(str(err))
                raise err

            encoder = getattr(module, structure_name)
            logger.debug("Successfully got encoder.")
            return encoder
        except (ModuleNotFoundError, ImportError):
            error_data = {"main_module": main_module, "service_name": service_name, "service_module": service_module}

            err = MapProofBuilderError("Incorrect module data", error_data)
            logger.warning("%s: %s", str(err), error_data)
            raise err
        except AttributeError:
            error_data = {"service_name": structure_name}

            err = MapProofBuilderError("Incorrect structure name", error_data)
            logger.warning("%s: %s", str(err), error_data)
            raise err

    def set_key_encoder(
        self,
        structure_name: str,
        main_module: Optional[str] = None,
        service_name: Optional[str] = None,
        service_module: Optional[str] = None,
    ) -> "MapProofBuilder":
        """
        Method to set the key encoder.

        If the Protobuf structure for the key lies in the main module,
        provide the `main_module` argument.
        Otherwise, provide both `service_name` and `service_module`.

        Parameters
        ----------
        structure_name: str
            Name of the Protobuf structure to be used in the converted function.
        main_module: Optional[str]
            Name of the main module.
        service_name: Optional[str]
            Name of the service.
        service_module: Optional[str]
            Name of the service module.

        Raises
        ------
        MapProofBuilderError
            If the provided data is incorrect, this exception rises.
        """
        self._key_encoder = self._get_encoder(structure_name, main_module, service_name, service_module)
        return self

    def set_value_encoder(
        self,
        structure_name: str,
        main_module: Optional[str] = None,
        service_name: Optional[str] = None,
        service_module: Optional[str] = None,
    ) -> "MapProofBuilder":
        """
        Method to set the value encoder.

        If the Protobuf structure for the value lies in the main module,
        provide the `main_module` argument.
        Otherwise, provide both `service_name` and `service_module`.

        Parameters
        ----------
        structure_name: str
            Name of the Protobuf structure to be used in the converted function.
        main_module: Optional[str]
            Name of the main module.
        service_name: Optional[str]
            Name of the service.
        service_module: Optional[str]
            Name of the service module.

        Raises
        ------
        MapProofBuilderError
            If the provided data is incorrect, this exception rises.
        """
        self._value_encoder = self._get_encoder(structure_name, main_module, service_name, service_module)

        return self

    def build_proof(self, proof: Dict[Any, Any]) -> MapProof:
        """
        Method to build MapProof from Dict[Any, Any].

        Call this method only after `set_key_encoder` and `set_value_encoder`.

        Parameters
        ----------
        proof: Dict[Any, Any]
            Raw ProofMap that will be parsed.

        Raises
        ------
        MapProofBuilderError
            If the method is called without prior `set_key_encoder` and `set_value_encoder` calls,
            this exception will rises.

        MalformedMapProofError
            If provided raw MapProof is malformed and parsing fails, this exception
            rises.
        """
        if not self._key_encoder or not self._value_encoder:
            err = MapProofBuilderError("Encoders are not set.")
            logger.warning(str(err))
            raise err

        key_encoder_func = build_encoder_function(self._key_encoder)
        value_encoder_func = build_encoder_function(self._value_encoder)

        return MapProof.parse(proof, key_encoder_func, value_encoder_func)
