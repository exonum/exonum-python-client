"""Module with the Bindings to Protoc."""
from typing import List, Optional
import os
import shutil
import subprocess

PROTOC_ENV_NAME = "PROTOC"


def _find_protoc() -> Optional[str]:
    if PROTOC_ENV_NAME in os.environ:
        return os.getenv(PROTOC_ENV_NAME)

    return shutil.which("protoc")


def _find_proto_files(path: str) -> List[str]:
    return [file for file in os.listdir(path) if file.endswith(".proto")]


class Protoc:
    """Class that provides an interface to protoc.
    It is not intended to be used in user code, see ProtobufLoader instead."""

    def __init__(self) -> None:
        protoc_path = _find_protoc()
        if protoc_path is None:
            print("Protobuf compiler not found")
            raise RuntimeError("protoc was not found, make sure that it is installed")

        self._protoc_path = protoc_path

    @staticmethod
    def _modify_file(path: str, modules: List[str]) -> None:
        # This method modifies imports in the generated files to be relative:
        with open(path, "rt") as file_in:
            file_content = file_in.readlines()

        with open(path, "wt") as file_out:
            for line in file_content:
                for module in modules:
                    line = line.replace("import {}_pb2 ".format(module), "from . import {}_pb2 ".format(module))
                file_out.write(line)

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
            print("Proto files were compiled successfully")
        else:
            print("Error acquired while compiling files: {}".format(stderr.decode("utf-8")))

        modules = [proto_path.replace(".proto", "") for proto_path in proto_files]
        for file in filter(lambda f: f.endswith(".py"), os.listdir(path_out)):
            self._modify_file("{}/{}".format(path_out, file), modules)
