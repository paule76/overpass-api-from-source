# gRPC Installation Guide

## Schnellstart

```bash
# 1. Repository klonen
git clone https://github.com/paule76/overpass-api-from-source.git
cd overpass-api-from-source

# 2. gRPC Docker Image bauen
docker build -f grpc/Dockerfile.grpc -t overpass-grpc:latest .

# 3. Container mit bestehender Datenbank starten
docker run -d --name overpass-grpc \
  -v overpass_db:/overpass_db_vol \
  -p 8092:80 \
  -p 50051:50051 \
  overpass-grpc:latest

# 4. Python Client testen
cd grpc
python3 -m venv venv
source venv/bin/activate
pip install grpcio grpcio-tools
python -m grpc_tools.protoc -I. --python_out=client --grpc_python_out=client overpass.proto
python client/test_grpc.py
```

## Docker Compose

```yaml
version: '3.8'
services:
  overpass-grpc:
    image: overpass-grpc:latest
    ports:
      - "8092:80"      # Legacy HTTP API
      - "50051:50051"  # gRPC API
    volumes:
      - overpass_db:/overpass_db_vol
    restart: unless-stopped
    
volumes:
  overpass_db:
    external: true
```

## Entwicklung

### C++ Server anpassen

1. Code in `grpc/server/grpc_server.cpp` bearbeiten
2. Image neu bauen: `docker build -f grpc/Dockerfile.grpc -t overpass-grpc:dev .`
3. Container neu starten

### Protobuf Schema erweitern

1. `grpc/overpass.proto` bearbeiten
2. C++ Code neu generieren (passiert automatisch beim Docker Build)
3. Python Code neu generieren:
   ```bash
   python -m grpc_tools.protoc -I. --python_out=client --grpc_python_out=client overpass.proto
   ```

## Integration in bestehende Projekte

### Python
```python
# requirements.txt
grpcio==1.74.0
protobuf==6.31.1
```

### Node.js
```bash
npm install @grpc/grpc-js @grpc/proto-loader
```

### Go
```bash
go get google.golang.org/grpc
go get google.golang.org/protobuf
```

## Performance Tuning

### Container Ressourcen
```bash
docker run -d --name overpass-grpc \
  --memory="8g" \
  --cpus="4" \
  -v overpass_db:/overpass_db_vol \
  -p 8092:80 \
  -p 50051:50051 \
  overpass-grpc:latest
```

### gRPC Server Optimierungen
Der Server ist bereits optimiert mit:
- Max Message Size: 100 MB
- Keep-Alive: 10s
- Multi-Threading Support

## Monitoring

### Health Check
```bash
# HTTP API
curl http://localhost:8092/health

# gRPC (mit grpcurl)
grpcurl -plaintext localhost:50051 grpc.health.v1.Health/Check
```

### Logs
```bash
docker logs -f overpass-grpc
```

## Sicherheit

### TLS aktivieren

1. Zertifikate generieren
2. nginx Config anpassen in `nginx-grpc.conf`
3. gRPC Server mit TLS Credentials starten

### Firewall
```bash
# Nur lokaler Zugriff
iptables -A INPUT -p tcp --dport 50051 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 50051 -j DROP
```