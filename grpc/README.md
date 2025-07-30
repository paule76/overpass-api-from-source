# Overpass gRPC/Protobuf Integration

## Architektur-Übersicht

```
┌─────────────┐     gRPC      ┌──────────────┐     HTTP/FastCGI    ┌─────────────┐
│   Client    │──────────────►│  gRPC Proxy  │───────────────────►│  Overpass   │
│ (Protobuf)  │◄──────────────│   (Go/Rust)  │◄───────────────────│     API     │
└─────────────┘    Streaming   └──────────────┘     JSON/XML       └─────────────┘
```

## Vorteile

1. **Bandbreite**: 60-80% Reduktion durch binäres Format
2. **Performance**: 3-10x schnelleres Parsing
3. **Streaming**: Große Resultate ohne Memory-Explosion
4. **Typsicherheit**: Compile-time Validierung

## Implementierungs-Phasen

### Phase 1: Proxy Layer (Quick Win)
- gRPC Server in Go/Rust
- Übersetzt Overpass JSON → Protobuf
- Keine Änderungen am Overpass Core
- ~2-4 Wochen Entwicklung

### Phase 2: Native Streaming
- Stream-Parser für Overpass Output
- Chunked Protobuf Responses
- Parallele Verarbeitung
- ~4-6 Wochen

### Phase 3: Native Integration (Langfristig)
- C++ gRPC in Overpass Core
- Direkte Protobuf Serialisierung
- Maximale Performance
- ~3-6 Monate

## Beispiel-Größenvergleich

### Node in JSON (Original)
```json
{
  "type": "node",
  "id": 123456789,
  "lat": 48.123456,
  "lon": 11.654321,
  "tags": {
    "name": "Marienplatz",
    "place": "square"
  }
}
```
**Größe: ~140 Bytes**

### Node in Protobuf
```
08 95 9E C4 3A    // id: 123456789
11 33 33 33 33    // lat: 48.123456 (double)
33 1F 48 40
19 52 B8 1E 85    // lon: 11.654321 (double)
EB 51 D4 26 40
22 0B 4D 61 72    // tags["name"] = "Marienplatz"
69 65 6E 70 6C
61 74 7A
22 0C 70 6C 61    // tags["place"] = "square"
63 65 06 73 71
75 61 72 65
```
**Größe: ~45 Bytes (68% kleiner!)**

## Performance-Messungen (geschätzt)

| Operation | JSON/HTTP | gRPC/Protobuf | Verbesserung |
|-----------|-----------|---------------|--------------|
| 10k Nodes serialisieren | 120ms | 15ms | 8x |
| 10k Nodes übertragen | 1.4MB | 450KB | 3x |
| 10k Nodes parsen | 80ms | 10ms | 8x |
| Streaming 100k Nodes | OOM | 50MB RAM | ✓ |

## Beispiel-Client (Go)

```go
func QueryOverpass(client overpass.OverpassAPIClient, query string) {
    // Streaming query
    stream, err := client.StreamQuery(context.Background(), &overpass.QueryRequest{
        Query: query,
        Timeout: 300,
    })
    
    for {
        element, err := stream.Recv()
        if err == io.EOF {
            break
        }
        
        switch elem := element.Element.(type) {
        case *overpass.Element_Node:
            fmt.Printf("Node %d at %.6f,%.6f\n", 
                elem.Node.Id, elem.Node.Lat, elem.Node.Lon)
        case *overpass.Element_Way:
            fmt.Printf("Way %d with %d nodes\n", 
                elem.Way.Id, len(elem.Way.NodeRefs))
        }
    }
}
```

## Docker Integration

```dockerfile
# Proxy als Sidecar Container
services:
  overpass:
    image: overpass-api-from-source:latest
    # ... existing config ...
    
  grpc-proxy:
    build: ./grpc
    ports:
      - "50051:50051"  # gRPC port
    environment:
      - OVERPASS_URL=http://overpass:80
    depends_on:
      - overpass
```

## Nächste Schritte

1. **Prototyp bauen** (Go-basierter Proxy)
2. **Benchmarks** mit echten Daten
3. **Client Libraries** generieren (Python, JS, Java)
4. **Community Feedback** einholen