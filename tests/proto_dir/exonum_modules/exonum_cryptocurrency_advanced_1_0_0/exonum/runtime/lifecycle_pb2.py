# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: exonum/runtime/lifecycle.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from .. import blockchain_pb2 as exonum_dot_blockchain__pb2
from ..crypto import types_pb2 as exonum_dot_crypto_dot_types__pb2
from . import base_pb2 as exonum_dot_runtime_dot_base__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='exonum/runtime/lifecycle.proto',
  package='exonum.runtime',
  syntax='proto3',
  serialized_options=b'\n com.exonum.messages.core.runtime',
  serialized_pb=b'\n\x1e\x65xonum/runtime/lifecycle.proto\x12\x0e\x65xonum.runtime\x1a\x17\x65xonum/blockchain.proto\x1a\x19\x65xonum/crypto/types.proto\x1a\x19\x65xonum/runtime/base.proto\"^\n\x12InstanceInitParams\x12\x33\n\rinstance_spec\x18\x01 \x01(\x0b\x32\x1c.exonum.runtime.InstanceSpec\x12\x13\n\x0b\x63onstructor\x18\x02 \x01(\x0c\"\xa9\x01\n\rGenesisConfig\x12(\n\x10\x63onsensus_config\x18\x01 \x01(\x0b\x32\x0e.exonum.Config\x12/\n\tartifacts\x18\x02 \x03(\x0b\x32\x1c.exonum.runtime.ArtifactSpec\x12=\n\x11\x62uiltin_instances\x18\x03 \x03(\x0b\x32\".exonum.runtime.InstanceInitParams\"\x87\x01\n\rArtifactState\x12\x13\n\x0b\x64\x65ploy_spec\x18\x01 \x01(\x0c\x12\x34\n\x06status\x18\x02 \x01(\x0e\x32$.exonum.runtime.ArtifactState.Status\"+\n\x06Status\x12\x08\n\x04NONE\x10\x00\x12\x0b\n\x07PENDING\x10\x01\x12\n\n\x06\x41\x43TIVE\x10\x02\"\xb8\x01\n\x0eInstanceStatus\x12\x37\n\x06simple\x18\x01 \x01(\x0e\x32%.exonum.runtime.InstanceStatus.SimpleH\x00\x12\x36\n\tmigration\x18\x02 \x01(\x0b\x32!.exonum.runtime.InstanceMigrationH\x00\"+\n\x06Simple\x12\x08\n\x04NONE\x10\x00\x12\n\n\x06\x41\x43TIVE\x10\x01\x12\x0b\n\x07STOPPED\x10\x02\x42\x08\n\x06status\"\x81\x01\n\x11InstanceMigration\x12*\n\x06target\x18\x01 \x01(\x0b\x32\x1a.exonum.runtime.ArtifactId\x12\x13\n\x0b\x65nd_version\x18\x02 \x01(\t\x12+\n\x0e\x63ompleted_hash\x18\x03 \x01(\x0b\x32\x13.exonum.crypto.Hash\"\xb9\x01\n\rInstanceState\x12*\n\x04spec\x18\x01 \x01(\x0b\x32\x1c.exonum.runtime.InstanceSpec\x12.\n\x06status\x18\x02 \x01(\x0b\x32\x1e.exonum.runtime.InstanceStatus\x12\x36\n\x0epending_status\x18\x03 \x01(\x0b\x32\x1e.exonum.runtime.InstanceStatus\x12\x14\n\x0c\x64\x61ta_version\x18\x04 \x01(\t\"Q\n\x0fMigrationStatus\x12#\n\x04hash\x18\x01 \x01(\x0b\x32\x13.exonum.crypto.HashH\x00\x12\x0f\n\x05\x65rror\x18\x02 \x01(\tH\x00\x42\x08\n\x06resultB\"\n com.exonum.messages.core.runtimeb\x06proto3'
  ,
  dependencies=[exonum_dot_blockchain__pb2.DESCRIPTOR,exonum_dot_crypto_dot_types__pb2.DESCRIPTOR,exonum_dot_runtime_dot_base__pb2.DESCRIPTOR,])



_ARTIFACTSTATE_STATUS = _descriptor.EnumDescriptor(
  name='Status',
  full_name='exonum.runtime.ArtifactState.Status',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='NONE', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='PENDING', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ACTIVE', index=2, number=2,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=490,
  serialized_end=533,
)
_sym_db.RegisterEnumDescriptor(_ARTIFACTSTATE_STATUS)

_INSTANCESTATUS_SIMPLE = _descriptor.EnumDescriptor(
  name='Simple',
  full_name='exonum.runtime.InstanceStatus.Simple',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='NONE', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ACTIVE', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='STOPPED', index=2, number=2,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=667,
  serialized_end=710,
)
_sym_db.RegisterEnumDescriptor(_INSTANCESTATUS_SIMPLE)


_INSTANCEINITPARAMS = _descriptor.Descriptor(
  name='InstanceInitParams',
  full_name='exonum.runtime.InstanceInitParams',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='instance_spec', full_name='exonum.runtime.InstanceInitParams.instance_spec', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='constructor', full_name='exonum.runtime.InstanceInitParams.constructor', index=1,
      number=2, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
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
  serialized_start=129,
  serialized_end=223,
)


_GENESISCONFIG = _descriptor.Descriptor(
  name='GenesisConfig',
  full_name='exonum.runtime.GenesisConfig',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='consensus_config', full_name='exonum.runtime.GenesisConfig.consensus_config', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='artifacts', full_name='exonum.runtime.GenesisConfig.artifacts', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='builtin_instances', full_name='exonum.runtime.GenesisConfig.builtin_instances', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
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
  serialized_start=226,
  serialized_end=395,
)


_ARTIFACTSTATE = _descriptor.Descriptor(
  name='ArtifactState',
  full_name='exonum.runtime.ArtifactState',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='deploy_spec', full_name='exonum.runtime.ArtifactState.deploy_spec', index=0,
      number=1, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='status', full_name='exonum.runtime.ArtifactState.status', index=1,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _ARTIFACTSTATE_STATUS,
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=398,
  serialized_end=533,
)


_INSTANCESTATUS = _descriptor.Descriptor(
  name='InstanceStatus',
  full_name='exonum.runtime.InstanceStatus',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='simple', full_name='exonum.runtime.InstanceStatus.simple', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='migration', full_name='exonum.runtime.InstanceStatus.migration', index=1,
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
    _INSTANCESTATUS_SIMPLE,
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='status', full_name='exonum.runtime.InstanceStatus.status',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=536,
  serialized_end=720,
)


_INSTANCEMIGRATION = _descriptor.Descriptor(
  name='InstanceMigration',
  full_name='exonum.runtime.InstanceMigration',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='target', full_name='exonum.runtime.InstanceMigration.target', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='end_version', full_name='exonum.runtime.InstanceMigration.end_version', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='completed_hash', full_name='exonum.runtime.InstanceMigration.completed_hash', index=2,
      number=3, type=11, cpp_type=10, label=1,
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
  serialized_start=723,
  serialized_end=852,
)


_INSTANCESTATE = _descriptor.Descriptor(
  name='InstanceState',
  full_name='exonum.runtime.InstanceState',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='spec', full_name='exonum.runtime.InstanceState.spec', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='status', full_name='exonum.runtime.InstanceState.status', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='pending_status', full_name='exonum.runtime.InstanceState.pending_status', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='data_version', full_name='exonum.runtime.InstanceState.data_version', index=3,
      number=4, type=9, cpp_type=9, label=1,
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
  serialized_start=855,
  serialized_end=1040,
)


_MIGRATIONSTATUS = _descriptor.Descriptor(
  name='MigrationStatus',
  full_name='exonum.runtime.MigrationStatus',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='hash', full_name='exonum.runtime.MigrationStatus.hash', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='error', full_name='exonum.runtime.MigrationStatus.error', index=1,
      number=2, type=9, cpp_type=9, label=1,
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
    _descriptor.OneofDescriptor(
      name='result', full_name='exonum.runtime.MigrationStatus.result',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=1042,
  serialized_end=1123,
)

_INSTANCEINITPARAMS.fields_by_name['instance_spec'].message_type = exonum_dot_runtime_dot_base__pb2._INSTANCESPEC
_GENESISCONFIG.fields_by_name['consensus_config'].message_type = exonum_dot_blockchain__pb2._CONFIG
_GENESISCONFIG.fields_by_name['artifacts'].message_type = exonum_dot_runtime_dot_base__pb2._ARTIFACTSPEC
_GENESISCONFIG.fields_by_name['builtin_instances'].message_type = _INSTANCEINITPARAMS
_ARTIFACTSTATE.fields_by_name['status'].enum_type = _ARTIFACTSTATE_STATUS
_ARTIFACTSTATE_STATUS.containing_type = _ARTIFACTSTATE
_INSTANCESTATUS.fields_by_name['simple'].enum_type = _INSTANCESTATUS_SIMPLE
_INSTANCESTATUS.fields_by_name['migration'].message_type = _INSTANCEMIGRATION
_INSTANCESTATUS_SIMPLE.containing_type = _INSTANCESTATUS
_INSTANCESTATUS.oneofs_by_name['status'].fields.append(
  _INSTANCESTATUS.fields_by_name['simple'])
_INSTANCESTATUS.fields_by_name['simple'].containing_oneof = _INSTANCESTATUS.oneofs_by_name['status']
_INSTANCESTATUS.oneofs_by_name['status'].fields.append(
  _INSTANCESTATUS.fields_by_name['migration'])
_INSTANCESTATUS.fields_by_name['migration'].containing_oneof = _INSTANCESTATUS.oneofs_by_name['status']
_INSTANCEMIGRATION.fields_by_name['target'].message_type = exonum_dot_runtime_dot_base__pb2._ARTIFACTID
_INSTANCEMIGRATION.fields_by_name['completed_hash'].message_type = exonum_dot_crypto_dot_types__pb2._HASH
_INSTANCESTATE.fields_by_name['spec'].message_type = exonum_dot_runtime_dot_base__pb2._INSTANCESPEC
_INSTANCESTATE.fields_by_name['status'].message_type = _INSTANCESTATUS
_INSTANCESTATE.fields_by_name['pending_status'].message_type = _INSTANCESTATUS
_MIGRATIONSTATUS.fields_by_name['hash'].message_type = exonum_dot_crypto_dot_types__pb2._HASH
_MIGRATIONSTATUS.oneofs_by_name['result'].fields.append(
  _MIGRATIONSTATUS.fields_by_name['hash'])
_MIGRATIONSTATUS.fields_by_name['hash'].containing_oneof = _MIGRATIONSTATUS.oneofs_by_name['result']
_MIGRATIONSTATUS.oneofs_by_name['result'].fields.append(
  _MIGRATIONSTATUS.fields_by_name['error'])
_MIGRATIONSTATUS.fields_by_name['error'].containing_oneof = _MIGRATIONSTATUS.oneofs_by_name['result']
DESCRIPTOR.message_types_by_name['InstanceInitParams'] = _INSTANCEINITPARAMS
DESCRIPTOR.message_types_by_name['GenesisConfig'] = _GENESISCONFIG
DESCRIPTOR.message_types_by_name['ArtifactState'] = _ARTIFACTSTATE
DESCRIPTOR.message_types_by_name['InstanceStatus'] = _INSTANCESTATUS
DESCRIPTOR.message_types_by_name['InstanceMigration'] = _INSTANCEMIGRATION
DESCRIPTOR.message_types_by_name['InstanceState'] = _INSTANCESTATE
DESCRIPTOR.message_types_by_name['MigrationStatus'] = _MIGRATIONSTATUS
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

InstanceInitParams = _reflection.GeneratedProtocolMessageType('InstanceInitParams', (_message.Message,), {
  'DESCRIPTOR' : _INSTANCEINITPARAMS,
  '__module__' : 'exonum.runtime.lifecycle_pb2'
  # @@protoc_insertion_point(class_scope:exonum.runtime.InstanceInitParams)
  })
_sym_db.RegisterMessage(InstanceInitParams)

GenesisConfig = _reflection.GeneratedProtocolMessageType('GenesisConfig', (_message.Message,), {
  'DESCRIPTOR' : _GENESISCONFIG,
  '__module__' : 'exonum.runtime.lifecycle_pb2'
  # @@protoc_insertion_point(class_scope:exonum.runtime.GenesisConfig)
  })
_sym_db.RegisterMessage(GenesisConfig)

ArtifactState = _reflection.GeneratedProtocolMessageType('ArtifactState', (_message.Message,), {
  'DESCRIPTOR' : _ARTIFACTSTATE,
  '__module__' : 'exonum.runtime.lifecycle_pb2'
  # @@protoc_insertion_point(class_scope:exonum.runtime.ArtifactState)
  })
_sym_db.RegisterMessage(ArtifactState)

InstanceStatus = _reflection.GeneratedProtocolMessageType('InstanceStatus', (_message.Message,), {
  'DESCRIPTOR' : _INSTANCESTATUS,
  '__module__' : 'exonum.runtime.lifecycle_pb2'
  # @@protoc_insertion_point(class_scope:exonum.runtime.InstanceStatus)
  })
_sym_db.RegisterMessage(InstanceStatus)

InstanceMigration = _reflection.GeneratedProtocolMessageType('InstanceMigration', (_message.Message,), {
  'DESCRIPTOR' : _INSTANCEMIGRATION,
  '__module__' : 'exonum.runtime.lifecycle_pb2'
  # @@protoc_insertion_point(class_scope:exonum.runtime.InstanceMigration)
  })
_sym_db.RegisterMessage(InstanceMigration)

InstanceState = _reflection.GeneratedProtocolMessageType('InstanceState', (_message.Message,), {
  'DESCRIPTOR' : _INSTANCESTATE,
  '__module__' : 'exonum.runtime.lifecycle_pb2'
  # @@protoc_insertion_point(class_scope:exonum.runtime.InstanceState)
  })
_sym_db.RegisterMessage(InstanceState)

MigrationStatus = _reflection.GeneratedProtocolMessageType('MigrationStatus', (_message.Message,), {
  'DESCRIPTOR' : _MIGRATIONSTATUS,
  '__module__' : 'exonum.runtime.lifecycle_pb2'
  # @@protoc_insertion_point(class_scope:exonum.runtime.MigrationStatus)
  })
_sym_db.RegisterMessage(MigrationStatus)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
