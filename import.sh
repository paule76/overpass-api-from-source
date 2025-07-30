#!/bin/bash
set -e

echo "Starting OSM data import..."
cd /overpass_db_vol

# Clean up old database
rm -rf db
mkdir -p db

# Find first .osm.bz2 file in data directory
OSM_FILE=$(find /data -name "*.osm.bz2" -type f | head -n1)

if [ -z "$OSM_FILE" ]; then
  echo "ERROR: No .osm.bz2 file found in overpass-data directory!"
  exit 1
fi

echo "Importing: $OSM_FILE"
echo "This may take several minutes depending on file size..."

# Run the import
/opt/overpass/bin/init_osm3s.sh "$OSM_FILE" /overpass_db_vol/db /opt/overpass --meta=no

echo "Import completed!"