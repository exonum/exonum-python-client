import os
import shutil
import subprocess

PROTOC_ENV_NAME = "PROTOC"


def find_protoc():
    if PROTOC_ENV_NAME in os.environ:
        return os.getenv(PROTOC_ENV_NAME)
    else:
        return shutil.which("protoc")


def find_proto_files(path):
    return [file for file in os.listdir(path) if file.endswith(".proto")]


class Protoc:
    def __init__(self):
        self.protoc_path = find_protoc()
        # TODO raise exception and handle in user code?
        if self.protoc_path is None:
            print("Protobuf compiler not found")
            exit(1)

    def _modify_file(self, path, modules):
        with open(path, "rt") as file_in:
            file_content = file_in.readlines()

        with open(path, "wt") as file_out:
            for line in file_content:
                for module in modules:
                    line = line.replace(
                        "import {}_pb2 ".format(module),
                        "from . import {}_pb2 ".format(module),
                    )
                file_out.write(line)

    def compile(self, path_in, path_out, include=None):
        os.makedirs(path_out)

        init_file_path = os.path.join(path_out, '__init__.py')
        open(init_file_path, 'a').close()

        protoc_args = None
        if include:
            protoc_args = [
                self.protoc_path,
                "--proto_path={}".format(path_in),
                "--proto_path={}".format(include),
                "--python_out={}".format(path_out),
            ]
        else:
            protoc_args = [
                self.protoc_path,
                "--proto_path={}".format(path_in),
                "--python_out={}".format(path_out),
            ]

        proto_files = find_proto_files(path_in)
        if include:
            proto_files.extend(find_proto_files(include))
        protoc_args.extend(proto_files)
        protoc_process = subprocess.Popen(
            protoc_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        code = protoc_process.wait()
        (stdout, stderr) = protoc_process.communicate()
        if code == 0:
            print("Proto files were compiled successfully")
        else:
            print("Error acquired while compiling files: {}".format(stderr.decode("utf-8")))

        modules = [proto_path.replace(".proto", "") for proto_path in proto_files]
        for file in filter(lambda f: f.endswith(".py"), os.listdir(path_out)):
            self._modify_file("{}/{}".format(path_out, file), modules)
