# pylint: disable=missing-docstring, protected-access
# type: ignore

import unittest
import sys
import os


class ModuleUserTestCase(unittest.TestCase):
    def setUp(self):
        pass


class PrecompiledModuleUserTestCase(ModuleUserTestCase):
    @classmethod
    def setUpClass(cls):
        # Add a folder with pre-compiled Protobuf messages to the path (so it can be imported):
        sys.path.append(os.path.abspath("tests/proto_dir"))

    @classmethod
    def tearDownClass(cls):
        # Remove the Protobuf directory from the path:
        sys.path.remove(os.path.abspath("tests/proto_dir"))
