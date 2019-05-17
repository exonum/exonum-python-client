import argparse
import os
import shutil
import subprocess

PROTOC_ENV_NAME = "PROTOC"
EXONUM_PROTO_PATH = "--proto_path={}/exonum/src/proto/schema/exonum"
SERVICE_PROTO_PATH = "--proto_path={}"
HELPERS_PROTO = "helpers.proto"


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="exonum-light-client", description="Exonum light client"
    )
    sub_parser = parser.add_subparsers(
        title="subcommands", help="Compiles proto files into Python equivalent"
    )
    parser_compile = sub_parser.add_parser("compile")
    parser_compile.add_argument(
        "-e",
        "--exonum-sources",
        type=str,
        help="A path to exonum's sources",
        required=True,
    )
    parser_compile.add_argument(
        "-s",
        "--service-path",
        type=str,
        help="A path to the directory with service's proto files",
        required=True,
    )
    parser_compile.add_argument(
        "-o",
        "--output",
        type=str,
        help="A path to the directory where compiled files should be saved",
        required=True,
    )

    return parser_compile.parse_args()


def find_protoc():
    if PROTOC_ENV_NAME in os.environ:
        return os.getenv(PROTOC_ENV_NAME)
    else:
        return shutil.which("protoc")


def find_proto_files(path):
    return [file for file in os.listdir(path) if file.endswith(".proto")]


def modify_file(path, modules):
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


def create_dir_if_not_exist(path):
    if not os.path.exists(path):
        os.makedirs(path)


def main():
    args = parse_arguments()
    path_to_protoc = find_protoc()

    if path_to_protoc is None:
        print("Protobuf compiler not found")
        exit(1)

    create_dir_if_not_exist(args.output)

    protoc_args = [
        path_to_protoc,
        EXONUM_PROTO_PATH.format(args.exonum_sources),
        SERVICE_PROTO_PATH.format(args.service_path),
        "--python_out={}".format(args.output),
    ]
    proto_files = find_proto_files(args.service_path)
    proto_files.append(HELPERS_PROTO)
    protoc_args.extend(proto_files)
    protoc_process = subprocess.Popen(
        protoc_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    code = protoc_process.wait()
    if code == 0:
        print("Proto files were compiled successfully")
    else:
        out, err = protoc_process.communicate()
        print("Error acquired while compiling files: {}".format(err.decode("utf-8")))

    modules = [proto_path.replace(".proto", "") for proto_path in proto_files]
    for file in filter(lambda f: f.endswith(".py"), os.listdir(args.output)):
        modify_file("{}/{}".format(args.output, file), proto_files)


if __name__ == "__main__":
    main()
