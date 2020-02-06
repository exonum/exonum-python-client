# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: exonum/doc_tests.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from .crypto import types_pb2 as exonum_dot_crypto_dot_types__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='exonum/doc_tests.proto',
  package='exonum.crypto.doc_tests',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=b'\n\x16\x65xonum/doc_tests.proto\x12\x17\x65xonum.crypto.doc_tests\x1a\x19\x65xonum/crypto/types.proto\"\x1c\n\x0c\x43reateWallet\x12\x0c\n\x04name\x18\x01 \x01(\t\"\x1d\n\x05Point\x12\t\n\x01x\x18\x01 \x01(\x05\x12\t\n\x01y\x18\x02 \x01(\x05\"\x05\n\x03TxA\"\x05\n\x03TxB\"=\n\rMyTransaction\x12,\n\npublic_key\x18\x01 \x01(\x0b\x32\x18.exonum.crypto.PublicKey\"_\n\rMyStructSmall\x12%\n\x03key\x18\x01 \x01(\x0b\x32\x18.exonum.crypto.PublicKey\x12\x11\n\tnum_field\x18\x02 \x01(\r\x12\x14\n\x0cstring_field\x18\x03 \x01(\t\"q\n\x0bMyStructBig\x12!\n\x04hash\x18\x01 \x01(\x0b\x32\x13.exonum.crypto.Hash\x12?\n\x0fmy_struct_small\x18\x02 \x01(\x0b\x32&.exonum.crypto.doc_tests.MyStructSmallb\x06proto3'
  ,
  dependencies=[exonum_dot_crypto_dot_types__pb2.DESCRIPTOR,])




_CREATEWALLET = _descriptor.Descriptor(
  name='CreateWallet',
  full_name='exonum.crypto.doc_tests.CreateWallet',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='exonum.crypto.doc_tests.CreateWallet.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=78,
  serialized_end=106,
)


_POINT = _descriptor.Descriptor(
  name='Point',
  full_name='exonum.crypto.doc_tests.Point',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='x', full_name='exonum.crypto.doc_tests.Point.x', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='y', full_name='exonum.crypto.doc_tests.Point.y', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=108,
  serialized_end=137,
)


_TXA = _descriptor.Descriptor(
  name='TxA',
  full_name='exonum.crypto.doc_tests.TxA',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=139,
  serialized_end=144,
)


_TXB = _descriptor.Descriptor(
  name='TxB',
  full_name='exonum.crypto.doc_tests.TxB',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=146,
  serialized_end=151,
)


_MYTRANSACTION = _descriptor.Descriptor(
  name='MyTransaction',
  full_name='exonum.crypto.doc_tests.MyTransaction',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='public_key', full_name='exonum.crypto.doc_tests.MyTransaction.public_key', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=153,
  serialized_end=214,
)


_MYSTRUCTSMALL = _descriptor.Descriptor(
  name='MyStructSmall',
  full_name='exonum.crypto.doc_tests.MyStructSmall',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='exonum.crypto.doc_tests.MyStructSmall.key', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='num_field', full_name='exonum.crypto.doc_tests.MyStructSmall.num_field', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='string_field', full_name='exonum.crypto.doc_tests.MyStructSmall.string_field', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=216,
  serialized_end=311,
)


_MYSTRUCTBIG = _descriptor.Descriptor(
  name='MyStructBig',
  full_name='exonum.crypto.doc_tests.MyStructBig',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='hash', full_name='exonum.crypto.doc_tests.MyStructBig.hash', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='my_struct_small', full_name='exonum.crypto.doc_tests.MyStructBig.my_struct_small', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=313,
  serialized_end=426,
)

_MYTRANSACTION.fields_by_name['public_key'].message_type = exonum_dot_crypto_dot_types__pb2._PUBLICKEY
_MYSTRUCTSMALL.fields_by_name['key'].message_type = exonum_dot_crypto_dot_types__pb2._PUBLICKEY
_MYSTRUCTBIG.fields_by_name['hash'].message_type = exonum_dot_crypto_dot_types__pb2._HASH
_MYSTRUCTBIG.fields_by_name['my_struct_small'].message_type = _MYSTRUCTSMALL
DESCRIPTOR.message_types_by_name['CreateWallet'] = _CREATEWALLET
DESCRIPTOR.message_types_by_name['Point'] = _POINT
DESCRIPTOR.message_types_by_name['TxA'] = _TXA
DESCRIPTOR.message_types_by_name['TxB'] = _TXB
DESCRIPTOR.message_types_by_name['MyTransaction'] = _MYTRANSACTION
DESCRIPTOR.message_types_by_name['MyStructSmall'] = _MYSTRUCTSMALL
DESCRIPTOR.message_types_by_name['MyStructBig'] = _MYSTRUCTBIG
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

CreateWallet = _reflection.GeneratedProtocolMessageType('CreateWallet', (_message.Message,), {
  'DESCRIPTOR' : _CREATEWALLET,
  '__module__' : 'exonum.doc_tests_pb2'
  # @@protoc_insertion_point(class_scope:exonum.crypto.doc_tests.CreateWallet)
  })
_sym_db.RegisterMessage(CreateWallet)

Point = _reflection.GeneratedProtocolMessageType('Point', (_message.Message,), {
  'DESCRIPTOR' : _POINT,
  '__module__' : 'exonum.doc_tests_pb2'
  # @@protoc_insertion_point(class_scope:exonum.crypto.doc_tests.Point)
  })
_sym_db.RegisterMessage(Point)

TxA = _reflection.GeneratedProtocolMessageType('TxA', (_message.Message,), {
  'DESCRIPTOR' : _TXA,
  '__module__' : 'exonum.doc_tests_pb2'
  # @@protoc_insertion_point(class_scope:exonum.crypto.doc_tests.TxA)
  })
_sym_db.RegisterMessage(TxA)

TxB = _reflection.GeneratedProtocolMessageType('TxB', (_message.Message,), {
  'DESCRIPTOR' : _TXB,
  '__module__' : 'exonum.doc_tests_pb2'
  # @@protoc_insertion_point(class_scope:exonum.crypto.doc_tests.TxB)
  })
_sym_db.RegisterMessage(TxB)

MyTransaction = _reflection.GeneratedProtocolMessageType('MyTransaction', (_message.Message,), {
  'DESCRIPTOR' : _MYTRANSACTION,
  '__module__' : 'exonum.doc_tests_pb2'
  # @@protoc_insertion_point(class_scope:exonum.crypto.doc_tests.MyTransaction)
  })
_sym_db.RegisterMessage(MyTransaction)

MyStructSmall = _reflection.GeneratedProtocolMessageType('MyStructSmall', (_message.Message,), {
  'DESCRIPTOR' : _MYSTRUCTSMALL,
  '__module__' : 'exonum.doc_tests_pb2'
  # @@protoc_insertion_point(class_scope:exonum.crypto.doc_tests.MyStructSmall)
  })
_sym_db.RegisterMessage(MyStructSmall)

MyStructBig = _reflection.GeneratedProtocolMessageType('MyStructBig', (_message.Message,), {
  'DESCRIPTOR' : _MYSTRUCTBIG,
  '__module__' : 'exonum.doc_tests_pb2'
  # @@protoc_insertion_point(class_scope:exonum.crypto.doc_tests.MyStructBig)
  })
_sym_db.RegisterMessage(MyStructBig)


# @@protoc_insertion_point(module_scope)