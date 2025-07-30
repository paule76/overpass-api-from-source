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

# Find all .osm.bz2 files in data directory
OSM_FILES=($(find /data -name "*.osm.bz2" -type f | sort))
FILE_COUNT=${#OSM_FILES[@]}

if [ $FILE_COUNT -eq 0 ]; then
  echo "ERROR: No .osm.bz2 file found in overpass-data directory!"
  exit 1
elif [ $FILE_COUNT -eq 1 ]; then
  # Single file - import directly
  OSM_FILE="${OSM_FILES[0]}"
  echo "Importing single file: $OSM_FILE"
  echo "This may take several minutes to hours depending on file size..."
  /opt/overpass/bin/init_osm3s.sh "$OSM_FILE" /overpass_db_vol/db /opt/overpass --meta=no
else
  # Multiple files - merge first
  echo "Found $FILE_COUNT OSM files:"
  for file in "${OSM_FILES[@]}"; do
    echo "  - $(basename "$file") ($(du -h "$file" | cut -f1))"
  done
  
  # Check if osmium is available
  if ! command -v osmium &> /dev/null; then
    echo ""
    echo "ERROR: osmium-tool is not installed!"
    echo "Multiple files found but cannot merge without osmium."
    echo ""
    echo "Options:"
    echo "1. Keep only one .osm.bz2 file in the data directory"
    echo "2. Rebuild the Docker image with the latest Dockerfile"
    exit 1
  fi
  
  echo ""
  echo "Merging files with osmium..."
  MERGED_FILE="/tmp/merged.osm.bz2"
  
  # Use osmium merge to combine all files
  osmium merge "${OSM_FILES[@]}" -o "$MERGED_FILE"
  
  if [ $? -ne 0 ]; then
    echo "ERROR: Failed to merge OSM files!"
    exit 1
  fi
  
  echo "Merge completed. Merged file size: $(du -h "$MERGED_FILE" | cut -f1)"
  
  # Optional: Check referential integrity
  if [ "${CHECK_REFS:-no}" = "yes" ]; then
    echo ""
    echo "Checking referential integrity..."
    osmium check-refs "$MERGED_FILE"
    if [ $? -ne 0 ]; then
      echo "WARNING: Referential integrity check found issues."
      echo "This is common with regional extracts that reference objects outside the region."
      echo "The import will continue..."
    else
      echo "Referential integrity check passed."
    fi
  fi
  echo "Importing merged data..."
  echo "This may take several hours depending on total size..."
  
  /opt/overpass/bin/init_osm3s.sh "$MERGED_FILE" /overpass_db_vol/db /opt/overpass --meta=no
  
  # Clean up merged file
  rm -f "$MERGED_FILE"
fi

echo "Import completed!"