import importlib

class ModuleManager:
    @staticmethod
    def import_main_module(self, module_name):
        module = importlib.import_module('exonum_modules.main.{}_pb2'.format(module_name))

        return module

    @staticmethod
    def import_service_module(self, service_name, module_name):
        service_module_name = re.sub(r'[-. /]', '_', service_name)
        module = importlib.import_module('exonum_modules.{}.{}_pb2'.format(service_module_name, module_name))

        return module
