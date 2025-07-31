#!/bin/bash

# Start nginx
service nginx start

# Start fcgiwrap with multiple workers (for legacy HTTP API)
spawn-fcgi -s /var/run/fcgiwrap.socket -F 12 -u www-data -g www-data /usr/sbin/fcgiwrap

# Check if database exists
if [ -f "/overpass_db_vol/db/nodes.bin" ]; then
    echo "Using existing database in /overpass_db_vol/db"
    DB_DIR="/overpass_db_vol/db"
else
    echo "No database found!"
    exit 1
fi

# Start Overpass dispatcher
echo "Starting Overpass dispatcher..."
/opt/overpass/bin/dispatcher --osm-base --db-dir=$DB_DIR &

# Wait for dispatcher to be ready
sleep 5

# Start gRPC server
echo "Starting gRPC server on port 50051..."
/opt/grpc-server/overpass-grpc-server &

# Keep container running and show logs
tail -f /dev/null