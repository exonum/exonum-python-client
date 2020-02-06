"""Module with the Bindings to Protoc."""
from typing import List, Optional
from logging import getLogger
import glob
import os
import re
import shutil
import subprocess

# pylint: disable=C0103
logger = getLogger(__name__)

PROTOC_ENV_NAME = "PROTOC"
PROTOC_MIN_VERSION = (3, 6, 1)


def _find_protoc() -> Optional[str]:
    if PROTOC_ENV_NAME in os.environ:
        return os.getenv(PROTOC_ENV_NAME)

    return shutil.which("protoc")


def _find_proto_files(path: str) -> List[str]:
    return glob.glob(path + "/**/*.proto", recursive=True)


class Protoc:
    """Class that provides an interface to protoc.
    It is not intended to be used in user code, see ProtobufLoader instead."""

    def __init__(self) -> None:
        protoc_path = _find_protoc()
        if protoc_path is None:
            logger.critical("Protobuf compiler not found.")
            raise RuntimeError("protoc was not found, make sure that it is installed")

        self._protoc_path = protoc_path

        self._ensure_protoc_version()

    @staticmethod
    def _modify_file(path: str, modules: List[str]) -> None:
        # This method modifies imports in the generated files to be relative:
        with open(path, "rt") as file_in:
            file_content = file_in.readlines()

        with open(path, "wt") as file_out:
            if "/exonum/proof/" in path or "/exonum/runtime/" in path:
                for line in file_content:
                    line = line.replace("from exonum import ", "from .. import ")
                    line = line.replace("from exonum.crypto import ", "from ..crypto import ")
                    line = line.replace("from exonum.runtime import ", "from . import ")
                    file_out.write(line)
                return

            if "/exonum/" in path:
                for line in file_content:
                    line = line.replace("from exonum import ", "from . import ")
                    line = line.replace("from exonum.crypto import ", "from .crypto import ")
                    line = line.replace("from exonum.runtime import ", "from .runtime import ")
                    line = line.replace("from exonum.proof import ", "from .proof import ")
                    file_out.write(line)
                return

            for line in file_content:
                for module in modules:
                    line = line.replace("from exonum", "from .exonum")
                    if line.startswith("import {}_pb2 ".format(module)):
                        line = line.replace("import {}_pb2 ".format(module), "from . import {}_pb2 ".format(module))
                file_out.write(line)

    def _ensure_protoc_version(self) -> None:
        """Checks that installed protoc has sufficient version."""
        protoc_args = [self._protoc_path, "--version"]
        version_stdout = subprocess.run(protoc_args, stdout=subprocess.PIPE, check=True).stdout

        # Convert bytestring to string and split into words.
        # b'libprotoc 3.7.1\n' => ['libprotoc', '3.7.1']
        version = version_stdout.decode("utf-8").strip().split()

        # Expected output is like 'libprotoc 3.7.1'
        if len(version) != 2 or not re.match(r"\d+.\d+.\d+", version[1]):
            raise RuntimeError(f"Unexpected output on resolving protoc version: {version}")

        # "3.7.1" => (3, 7, 1)
        parsed_version = tuple(map(int, version[1].split(".")))
        if parsed_version < PROTOC_MIN_VERSION:
            raise RuntimeError(
                f"Installed version of protoc is too old: {parsed_version}, install at least {PROTOC_MIN_VERSION}"
            )

    def compile(self, path_in: str, path_out: str, include: str = None) -> None:
        """Compiles .proto files from the `path_in` to `path_out` folder.

        Parameters
        ----------
        path_in: str
            Input folder.
        path_out: str
            Output folder.
        include: Optional[str]
            Includes.
        """
        os.makedirs(path_out)

        init_file_path = os.path.join(path_out, "__init__.py")
        open(init_file_path, "a").close()

        if include:
            protoc_args = [
                self._protoc_path,
                "--proto_path={}".format(path_in),
                "--proto_path={}".format(include),
                "--python_out={}".format(path_out),
            ]
        else:
            protoc_args = [self._protoc_path, "--proto_path={}".format(path_in), "--python_out={}".format(path_out)]

        proto_files = _find_proto_files(path_in)
        if include:
            proto_files.extend(_find_proto_files(include))
        protoc_args.extend(proto_files)
        protoc_process = subprocess.Popen(protoc_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        code = protoc_process.wait()
        (_, stderr) = protoc_process.communicate()
        if code == 0:
            logger.debug("Proto files were compiled successfully: %s", proto_files)
        else:
            logger.error("Error acquired while compiling files: %s. Files: %s.", stderr.decode("utf-8"), proto_files)

        modules = [proto_path.split("/")[-1].replace(".proto", "") for proto_path in proto_files]
        for file in glob.glob(path_out + "/**/*.py", recursive=True):
            open(os.path.join(os.path.split(file)[0], "__init__.py"), "a").close()
            self._modify_file(file, modules)
