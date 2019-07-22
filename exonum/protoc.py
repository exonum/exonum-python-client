
class Protoc:
	def __init__(self):
		pass

	def _modify_file(self, path):
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
		pass