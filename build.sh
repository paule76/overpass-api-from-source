#!/bin/bash

# Default version - can be overridden
OVERPASS_VERSION=${OVERPASS_VERSION:-0.7.62.7}

echo "Building Overpass API from source..."
echo "Version: $OVERPASS_VERSION"
echo ""

# Build the Docker image with the specified version
docker build \
  --build-arg OVERPASS_VERSION=$OVERPASS_VERSION \
  -t overpass-api-from-source:$OVERPASS_VERSION \
  -t overpass-api-from-source:latest \
  .

echo ""
echo "Build completed!"
echo ""
echo "To run the container:"
echo "docker compose --profile production up -d"
echo ""
echo "To build a different version:"
echo "OVERPASS_VERSION=0.7.62.6 ./build.sh"