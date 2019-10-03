import unittest
import os
import tempfile
import shutil

from exonum.protoc import Protoc


class TestProtoc(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="exonum_client_test_")
        self.out_dir = os.path.join(self.temp_dir, "python")
        self.main_proto_dir = os.path.abspath("tests/proto_dir/proto/main")
        self.service_proto_dir = os.path.abspath("tests/proto_dir/proto/exonum_cryptocurrency_advanced_0_11_0")

    def tearDown(self):
        shutil.rmtree(self.out_dir)

    def test_modules_compile_without_include(self):
        protoc = Protoc()

        protoc.compile(self.main_proto_dir, self.out_dir)

        input_sources = os.listdir(self.main_proto_dir)
        output_sources = os.listdir(self.out_dir)

        self.assertTrue("__init__.py" in output_sources)

        for file in input_sources:
            if file.endswith(".proto"):
                file_name = file.split(".")[0]

                expected_python_file = "{}_pb2.py".format(file_name)
                self.assertTrue(expected_python_file in output_sources)

    def test_modules_compile_with_include(self):
        protoc = Protoc()

        protoc.compile(self.service_proto_dir, self.out_dir, include=self.main_proto_dir)

        input_sources = os.listdir(self.service_proto_dir)
        main_sources = os.listdir(self.main_proto_dir)
        output_sources = os.listdir(self.out_dir)

        self.assertTrue("__init__.py" in output_sources)

        for file in input_sources + main_sources:
            if file.endswith(".proto"):
                file_name = file.split(".")[0]

                expected_python_file = "{}_pb2.py".format(file_name)
                self.assertTrue(expected_python_file in output_sources)

    # TODO add negative tests
