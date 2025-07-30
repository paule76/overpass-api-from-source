#!/bin/bash
# Generate Python code from protobuf definitions

echo "Generating Python protobuf code..."

# Create output directory
mkdir -p generated

# Generate Python code
python -m grpc_tools.protoc \
    -I../  \
    --python_out=generated/ \
    --pyi_out=generated/ \
    --grpc_python_out=generated/ \
    ../overpass.proto

# Fix imports (grpc_tools generates absolute imports)
sed -i 's/import overpass_pb2/from . import overpass_pb2/g' generated/overpass_pb2_grpc.py

echo "Generated files:"
ls -la generated/

echo "Done!"