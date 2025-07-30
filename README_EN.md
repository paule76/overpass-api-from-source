# Overpass API from Source

*[Deutsche README](README.md)*

A Docker container that compiles Overpass API directly from source code. Uses the latest version by default (as recommended by Overpass developers). Fixes known issues with the wiktorn/overpass-api image when processing regional OSM extracts.

## Problem

The official wiktorn/overpass-api Docker image has a bug when processing regional OSM extracts, resulting in `std::out_of_range` errors. This repository provides a working alternative.

## Features

- ✅ Compiled from official source code
- ✅ Flexible version selection (default: latest - always the newest version)
- ✅ No precompiled binaries - full transparency
- ✅ Fixes std::out_of_range errors with regional extracts
- ✅ Optimized for stability with C++ flags
- ✅ Nginx + FastCGI setup
- ✅ Docker Compose ready

## Quick Start

### Option A: Use Prebuilt Image (Recommended)
```bash
docker pull ghcr.io/paule76/overpass-api-from-source:latest
```

### Option B: Build from Source

#### 1. Clone Repository
```bash
git clone https://github.com/paule76/overpass-api-from-source.git
cd overpass-api-from-source
```

#### 2. Build Docker Image
```bash
# Default: Latest version (recommended)
./build.sh

# Or build specific version
OVERPASS_VERSION=0.7.62.7 ./build.sh
```

### 3. Prepare OSM Data

Create data directory and download OSM data:

```bash
mkdir -p overpass-data
cd overpass-data

# Example: Bremen (small, ~50MB, good for testing)
wget https://download.geofabrik.de/europe/germany/bremen-latest.osm.bz2

# Or: Luxembourg (~30MB)
wget https://download.geofabrik.de/europe/luxembourg-latest.osm.bz2

# Or: Malta (~20MB)
wget https://download.geofabrik.de/europe/malta-latest.osm.bz2

cd ..
```

**Recommendation**: Start with a small region like Bremen or Malta for testing. Import takes only a few minutes.

#### Estimated File Sizes and Import Times

| Region | File Size | Import Time* | Recommended For |
|--------|-----------|--------------|-----------------|
| Malta | ~20 MB | 1-2 min | First tests |
| Luxembourg | ~30 MB | 2-3 min | Tests |
| Bremen (DE) | ~50 MB | 2-5 min | Tests |
| Hamburg (DE) | ~90 MB | 5-10 min | Development |
| Berlin (DE) | ~120 MB | 10-15 min | Development |
| Bavaria (DE) | ~900 MB | 45-60 min | Production |
| Germany | ~3.5 GB | 3-4 hours | Production |

*Import times are estimates and depend on hardware.

All downloads at: https://download.geofabrik.de/

### 4. Initialize Database
```bash
# Create Docker volume
docker volume create overpass_db

# Import data (supports single or multiple .osm.bz2 files)
docker compose --profile import run --rm import

# NEW: Multi-Region Import!
# - Single file: Direct import
# - Multiple files: Automatic merging with osmium
#
# Tip: You can organize OSM files in subdirectories (e.g. overpass-data/backup/)
# The import script will find all files and merge them automatically

# With reference check (optional):
CHECK_REFS=yes docker compose --profile import run --rm import

# With existing database:
# - Interactive mode (default): Asks for confirmation
# - Force mode: IMPORT_MODE=force docker compose --profile import run --rm import
# - Skip mode: IMPORT_MODE=skip docker compose --profile import run --rm import
```

### 5. Start Overpass API
```bash
docker compose --profile production up -d
```

The API is then available at http://localhost:8091

## Usage

### Example Queries

**Check Status:**
```bash
curl http://localhost:8091/api/status
```

**Find Cities:**
```bash
curl -XPOST http://localhost:8091/api/interpreter \
  -d '[out:json];node["place"="city"]["name"="Berlin"];out;'
```

**POIs in Bounding Box:**
```bash
curl -XPOST http://localhost:8091/api/interpreter \
  -d '[out:json];node["amenity"="cafe"](52.5,13.3,52.6,13.4);out;'
```

## Repository Files

- `Dockerfile` - Build instructions for custom container
- `build.sh` - Build script
- `docker-compose.yml` - Docker Compose with profiles (production, import)
- `nginx.conf` - Nginx web server configuration
- `start.sh` - Container startup script
- `import.sh` - Database import script
- `overpass-data/` - Directory for OSM data (excluded from git)

## Configuration

### Build Configuration

Copy `.env.example` to `.env` and adjust values:

```bash
cp .env.example .env
```

Available versions at: https://dev.overpass-api.de/releases/

### Environment Variables

#### Build & Import
- `OVERPASS_VERSION` - Overpass API version (default: latest)
- `IMPORT_MODE` - Import behavior with existing DB: interactive, force, skip (default: interactive)
- `CHECK_REFS` - Check referential integrity during multi-region import (default: no)

#### Runtime
- `OVERPASS_META` - Enable metadata (default: no)
- `OVERPASS_SPACE` - Available space in bytes (default: 2000000000)
- `OVERPASS_MAX_TIMEOUT` - Maximum query timeout in seconds (default: 300)

### Ports

- `8091` - Overpass API endpoint

## Troubleshooting

**Container won't start:**
```bash
# Check logs
docker logs overpass_api

# Remove old socket files
docker run --rm -v overpass_db:/db alpine rm -f /db/db/osm3s_*
```

**Database errors:**
```bash
# Recreate volume
docker compose down
docker volume rm overpass_db
docker volume create overpass_db
# Then import data again
```

## License

The Overpass API is licensed under AGPL-3.0.
OSM data is licensed under ODbL.

## Credits

- Overpass API by Roland Olbricht
- Docker concept inspired by wiktorn/overpass-api project
- Developed with assistance from [Claude Code](https://claude.ai/code) 🤖

## Acknowledgment

Special thanks to Claude Code for patient assistance in debugging and developing this solution. This collaboration demonstrates how AI assistants can work together with humans to solve complex technical problems.