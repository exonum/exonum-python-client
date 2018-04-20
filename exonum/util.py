import sys


if sys.version_info.major < 3 or \
        (sys.version_info.major == 3 and sys.version_info.minor < 6):
    def make_class_ordered(cls):
        # https://www.python.org/dev/peps/pep-0520/
        from collections import OrderedDict
        cls.__prepare__ = classmethod(lambda *_: OrderedDict())
else:
    make_class_ordered = lambda _: None
