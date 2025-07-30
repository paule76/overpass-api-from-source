# Overpass API from Source

*[English README](README_EN.md)*

Ein Docker Container, der die Overpass API v0.7.62.7 direkt aus dem Quellcode kompiliert. Behebt bekannte Probleme des wiktorn/overpass-api Images mit regionalen OSM-Extracts.

## Problem

Das offizielle wiktorn/overpass-api Docker Image hat einen Bug beim Verarbeiten regionaler OSM-Extracts, der zu `std::out_of_range` Fehlern führt. Dieses Repository bietet eine funktionierende Alternative.

## Features

- ✅ Kompiliert aus offiziellem Quellcode
- ✅ Flexible Versionswahl (Standard: v0.7.62.7)
- ✅ Keine vorkompilierten Binaries - volle Transparenz
- ✅ Behebt std::out_of_range Fehler bei regionalen Extracts
- ✅ Optimiert für Stabilität mit C++ Flags
- ✅ Nginx + FastCGI Setup
- ✅ Docker Compose ready

## Schnellstart

### Option A: Vorgefertigtes Image verwenden (empfohlen)
```bash
docker pull ghcr.io/paule76/overpass-api-from-source:latest
```

### Option B: Selbst bauen

#### 1. Repository klonen
```bash
git clone https://github.com/paule76/overpass-api-from-source.git
cd overpass-api-from-source
```

#### 2. Docker Image bauen
```bash
# Standard-Version (0.7.62.7)
./build.sh

# Oder andere Version bauen
OVERPASS_VERSION=0.7.62.6 ./build.sh
```

### 3. OSM-Daten vorbereiten

Erstellen Sie den Datenordner und laden Sie OSM-Daten herunter:

```bash
mkdir -p overpass-data
cd overpass-data

# Beispiel: Bremen (klein, ~50MB, gut zum Testen)
wget https://download.geofabrik.de/europe/germany/bremen-latest.osm.bz2

# Oder: Saarland (~80MB)
wget https://download.geofabrik.de/europe/germany/saarland-latest.osm.bz2

# Oder: Berlin (~120MB)
wget https://download.geofabrik.de/europe/germany/berlin-latest.osm.bz2

cd ..
```

**Empfehlung**: Starten Sie mit einem kleinen Bundesland wie Bremen zum Testen. Der Import dauert nur wenige Minuten.

#### Geschätzte Dateigrößen und Import-Zeiten

| Bundesland | Dateigröße | Import-Zeit* | Empfohlen für |
|------------|------------|--------------|---------------|
| Bremen | ~50 MB | 2-5 Min | Erste Tests |
| Saarland | ~80 MB | 5-10 Min | Tests |
| Hamburg | ~90 MB | 5-10 Min | Tests |
| Berlin | ~120 MB | 10-15 Min | Entwicklung |
| Sachsen | ~300 MB | 20-30 Min | Entwicklung |
| Bayern | ~900 MB | 45-60 Min | Produktion |
| NRW | ~1.1 GB | 60-90 Min | Produktion |

*Import-Zeiten sind Schätzwerte und hängen von der Hardware ab.

Alle Downloads unter: https://download.geofabrik.de/europe/germany/

### 4. Datenbank initialisieren
```bash
# Docker Volume erstellen
docker volume create overpass_db

# Daten importieren (findet automatisch erste .osm.bz2 Datei, auch in Unterordnern)
docker compose --profile import run --rm import

# Tipp: Sie können OSM-Dateien in Unterordnern organisieren (z.B. overpass-data/backup/)
# Das Import-Script findet sie automatisch
```

### 5. Overpass API starten
```bash
docker compose --profile production up -d
```

Die API ist dann unter http://localhost:8090 erreichbar.

## Verwendung

### Beispiel-Abfragen

**Status prüfen:**
```bash
curl http://localhost:8090/api/status
```

**Städte finden:**
```bash
curl -XPOST http://localhost:8090/api/interpreter \
  -d '[out:json];node["place"="city"]["name"="München"];out;'
```

**POIs in Bounding Box:**
```bash
curl -XPOST http://localhost:8090/api/interpreter \
  -d '[out:json];node["amenity"="cafe"](48.1,11.5,48.2,11.6);out;'
```

## Dateien im Repository

- `Dockerfile` - Build-Anweisungen für den Custom Container
- `build.sh` - Script zum Bauen des Docker Images
- `docker-compose.yml` - Docker Compose mit Profilen (production, import)
- `nginx.conf` - Nginx Webserver Konfiguration
- `start.sh` - Container Startup Script
- `overpass-data/` - Ordner für OSM-Daten (nicht im Git)

## Konfiguration

### Build-Konfiguration

Kopieren Sie `.env.example` nach `.env` und passen Sie die Werte an:

```bash
cp .env.example .env
```

Verfügbare Versionen finden Sie unter: https://dev.overpass-api.de/releases/

### Umgebungsvariablen

- `OVERPASS_VERSION` - Overpass API Version (default: 0.7.62.7)
- `OVERPASS_META` - Metadaten aktivieren (default: no)
- `OVERPASS_SPACE` - Speicherplatz in Bytes (default: 2000000000)
- `OVERPASS_MAX_TIMEOUT` - Maximale Query-Timeout in Sekunden (default: 300)

### Ports

- `8090` - Overpass API Endpoint

## Troubleshooting

**Container startet nicht:**
```bash
# Logs prüfen
docker logs overpass_custom

# Alte Socket-Dateien löschen
docker run --rm -v overpass_db:/db alpine rm -f /db/db/osm3s_*
```

**Datenbank-Fehler:**
```bash
# Volume neu erstellen
docker compose down
docker volume rm overpass_db
docker volume create overpass_db
# Dann Daten neu importieren
```

## Lizenz

Die Overpass API steht unter der AGPL-3.0 Lizenz.
OSM-Daten stehen unter der ODbL Lizenz.

## Credits

- Overpass API von Roland Olbricht
- Docker-Konzept inspiriert vom wiktorn/overpass-api Projekt
- Entwickelt mit Unterstützung von [Claude Code](https://claude.ai/code) 🤖

## Danksagung

Ein besonderer Dank an Claude Code für die geduldige Unterstützung bei der Fehlersuche und Entwicklung dieser Lösung. Die Zusammenarbeit hat gezeigt, wie KI-Assistenten komplexe technische Probleme gemeinsam mit Menschen lösen können.