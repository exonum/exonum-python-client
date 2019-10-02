import unittest
import sys
import os


class ModuleUserTestCase(unittest.TestCase):
    def setUp(self):
        # Unload any previously loaded `exonum_main` modules from other tests:
        loaded_modules = list(sys.modules.keys())
        for module in loaded_modules:
            if module.startswith("exonum_modules"):
                del sys.modules[module]


class PrecompiledModuleUserTestCase(ModuleUserTestCase):
    @classmethod
    def setUpClass(cls):
        # Add a folder with pre-compiled Protobuf messages to the path (so it can be imported):
        sys.path.append(os.path.abspath("tests/proto_dir"))

    @classmethod
    def tearDownClass(self):
        # Remove the Protobuf directory from the path:
        sys.path.remove(os.path.abspath("tests/proto_dir"))
