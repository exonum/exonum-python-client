#!/bin/bash

PROTOC=protoc

MAIN_DIR=proto_dir/proto/main
PROTO_PATH=proto_dir/proto/main/exonum
SERVICE_DIR=proto_dir/proto/exonum_cryptocurrency_advanced_1_0_0

MAIN_OUT_DIR=proto_dir/exonum_modules/main
SERVICE_OUT_DIR=proto_dir/exonum_modules/exonum_cryptocurrency_advanced_1_0_0

# Main proto files
${PROTOC} -I${MAIN_DIR} --python_out=${MAIN_OUT_DIR} \
    ${PROTO_PATH}/*.proto \
    ${PROTO_PATH}/common/*.proto \
    ${PROTO_PATH}/crypto/*.proto \
    ${PROTO_PATH}/details/*.proto \
    ${PROTO_PATH}/proof/*.proto \
    ${PROTO_PATH}/runtime/*.proto

# Service proto files
${PROTOC} -I${MAIN_DIR} -I${SERVICE_DIR} --python_out=${SERVICE_OUT_DIR} \
    ${PROTO_PATH}/*.proto \
    ${PROTO_PATH}/common/*.proto \
    ${PROTO_PATH}/crypto/*.proto \
    ${PROTO_PATH}/details/*.proto \
    ${PROTO_PATH}/proof/*.proto \
    ${PROTO_PATH}/runtime/*.proto \
    proto_dir/proto/exonum_cryptocurrency_advanced_1_0_0/*.proto
