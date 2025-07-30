#!/bin/bash

# Default version - can be overridden
OVERPASS_VERSION=${OVERPASS_VERSION:-latest}

echo "Building Overpass API from source..."
echo "Version: $OVERPASS_VERSION"
echo ""

# Build the Docker image with the specified version
if [ "$OVERPASS_VERSION" = "latest" ]; then
  docker build \
    --build-arg OVERPASS_VERSION=$OVERPASS_VERSION \
    -t overpass-api-from-source:latest \
    .
else
  docker build \
    --build-arg OVERPASS_VERSION=$OVERPASS_VERSION \
    -t overpass-api-from-source:$OVERPASS_VERSION \
    -t overpass-api-from-source:latest \
    .
fi

echo ""
echo "Build completed!"
echo ""
echo "To run the container:"
echo "docker compose --profile production up -d"
echo ""
echo "To build a different version:"
echo "OVERPASS_VERSION=0.7.62.6 ./build.sh"