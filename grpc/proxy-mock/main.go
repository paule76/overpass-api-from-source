package main

import (
    "encoding/json"
    "fmt"
    "io"
    "log"
    "net/http"
    "strings"
)

type ProxyServer struct {
    overpassURL string
}

func (s *ProxyServer) handleQuery(w http.ResponseWriter, r *http.Request) {
    if r.Method != "POST" {
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
        return
    }

    // Read query from request
    body, err := io.ReadAll(r.Body)
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    var request struct {
        Query string `json:"query"`
    }
    if err := json.Unmarshal(body, &request); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    // Forward to Overpass
    overpassQuery := fmt.Sprintf("[out:json];%s", request.Query)
    resp, err := http.Post(
        s.overpassURL+"/api/interpreter",
        "application/x-www-form-urlencoded",
        strings.NewReader("data="+overpassQuery),
    )
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    defer resp.Body.Close()

    // Parse response
    var overpassResp map[string]interface{}
    if err := json.NewDecoder(resp.Body).Decode(&overpassResp); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    // Simulate protobuf benefits: add metadata
    response := map[string]interface{}{
        "elements": overpassResp["elements"],
        "metadata": map[string]interface{}{
            "format":            "protobuf-simulation",
            "original_size":     len(body),
            "compressed_size":   len(body) * 3 / 10, // Simulate 70% compression
            "compression_ratio": 0.7,
        },
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

func (s *ProxyServer) handleStatus(w http.ResponseWriter, r *http.Request) {
    status := map[string]interface{}{
        "status": "ok",
        "type":   "grpc-proxy-mock",
        "info":   "This is a mock gRPC proxy for testing",
        "benefits": map[string]interface{}{
            "bandwidth_reduction": "70%",
            "parsing_speed":       "8x faster",
            "streaming_support":   true,
        },
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(status)
}

func main() {
    overpassURL := "http://172.17.0.1:8091" // Docker host IP
    
    server := &ProxyServer{
        overpassURL: overpassURL,
    }

    http.HandleFunc("/query", server.handleQuery)
    http.HandleFunc("/status", server.handleStatus)

    log.Println("gRPC Mock Proxy listening on :50051")
    log.Printf("Forwarding to Overpass at %s", overpassURL)
    
    if err := http.ListenAndServe(":50051", nil); err != nil {
        log.Fatal(err)
    }
}