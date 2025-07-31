#!/bin/bash
# Generate Python protobuf files from overpass.proto

echo "Generating Python protobuf files..."

# Create output directory
mkdir -p generated

# Generate Python files
python -m grpc_tools.protoc \
    --proto_path=. \
    --python_out=generated \
    --grpc_python_out=generated \
    overpass.proto

echo "Generated files:"
ls -la generated/

echo "Done!"