#!/bin/bash

# Start nginx
service nginx start

# Start fcgiwrap with spawn-fcgi for better performance
# Multiple workers can handle concurrent requests
spawn-fcgi -s /var/run/fcgiwrap.socket -F 12 -u www-data -g www-data /usr/sbin/fcgiwrap

# Check if database exists
if [ -f "/overpass_db_vol/db/nodes.bin" ]; then
    echo "Using existing database in /overpass_db_vol/db"
    DB_DIR="/overpass_db_vol/db"
elif [ -f "/db/nodes.bin" ]; then
    echo "Using existing database in /db"
    DB_DIR="/db"
else
    echo "No database found. Looking for database files..."
    echo "Contents of /overpass_db_vol:"
    ls -la /overpass_db_vol/
    echo "Contents of /overpass_db_vol/db (if exists):"
    ls -la /overpass_db_vol/db/ 2>/dev/null || echo "Directory not found"
    exit 1
fi

# Start dispatcher
echo "Starting Overpass dispatcher..."
/opt/overpass/bin/dispatcher --osm-base --db-dir=$DB_DIR