#!/bin/bash
set -e

echo "Starting OSM data import..."
cd /overpass_db_vol

# Check import mode (default: interactive)
IMPORT_MODE=${IMPORT_MODE:-interactive}

# Check if database already exists
if [ -d "db" ] && [ "$(ls -A db 2>/dev/null)" ]; then
    echo "WARNING: Existing database found!"
    
    case "$IMPORT_MODE" in
        skip)
            echo "Skipping import (IMPORT_MODE=skip)"
            exit 0
            ;;
        force)
            echo "Removing existing database (IMPORT_MODE=force)"
            rm -rf db
            ;;
        interactive)
            echo "Do you want to delete the existing database and import new data?"
            echo "This will permanently delete all existing data!"
            echo "Type 'yes' to continue or anything else to abort:"
            read -t 30 -r response || response="timeout"
            
            if [ "$response" != "yes" ]; then
                echo "Import aborted. Existing database preserved."
                exit 0
            fi
            echo "Removing existing database..."
            rm -rf db
            ;;
        *)
            echo "ERROR: Invalid IMPORT_MODE: $IMPORT_MODE"
            echo "Valid options: interactive, force, skip"
            exit 1
            ;;
    esac
fi

# Create database directory
mkdir -p db

# Find first .osm.bz2 file in data directory
OSM_FILE=$(find /data -name "*.osm.bz2" -type f | head -n1)

if [ -z "$OSM_FILE" ]; then
  echo "ERROR: No .osm.bz2 file found in overpass-data directory!"
  exit 1
fi

echo "Importing: $OSM_FILE"
echo "This may take several minutes to hours depending on file size..."

# Run the import
/opt/overpass/bin/init_osm3s.sh "$OSM_FILE" /overpass_db_vol/db /opt/overpass --meta=no

echo "Import completed!"