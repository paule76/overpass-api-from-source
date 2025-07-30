package main

import (
    "context"
    "encoding/json"
    "fmt"
    "io"
    "log"
    "net"
    "net/http"
    "strings"
    "time"

    "google.golang.org/grpc"
    pb "github.com/paule76/overpass-grpc/api"
)

type server struct {
    pb.UnimplementedOverpassAPIServer
    overpassURL string
    httpClient  *http.Client
}

// Query implements standard non-streaming query
func (s *server) Query(ctx context.Context, req *pb.QueryRequest) (*pb.QueryResponse, error) {
    // Call Overpass API
    resp, err := s.callOverpass(req.Query, req.Timeout)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    // Parse JSON response
    var jsonResp overpassJSONResponse
    if err := json.NewDecoder(resp.Body).Decode(&jsonResp); err != nil {
        return nil, err
    }

    // Convert to protobuf
    pbResp := &pb.QueryResponse{
        Metadata: &pb.QueryMetadata{
            Generator: jsonResp.Generator,
            Copyright: jsonResp.OSM3S.Copyright,
        },
    }

    for _, elem := range jsonResp.Elements {
        pbElem := convertElement(elem)
        if pbElem != nil {
            pbResp.Elements = append(pbResp.Elements, pbElem)
        }
    }

    return pbResp, nil
}

// StreamQuery implements streaming query
func (s *server) StreamQuery(req *pb.QueryRequest, stream pb.OverpassAPI_StreamQueryServer) error {
    // Call Overpass API
    resp, err := s.callOverpass(req.Query, req.Timeout)
    if err != nil {
        return err
    }
    defer resp.Body.Close()

    // Stream parse JSON
    decoder := json.NewDecoder(resp.Body)
    
    // Read until we find "elements" array
    for {
        token, err := decoder.Token()
        if err != nil {
            return err
        }
        
        if key, ok := token.(string); ok && key == "elements" {
            // Start of array
            decoder.Token() // consume '['
            
            // Stream each element
            for decoder.More() {
                var elem overpassElement
                if err := decoder.Decode(&elem); err != nil {
                    return err
                }
                
                pbElem := convertElement(elem)
                if pbElem != nil {
                    if err := stream.Send(pbElem); err != nil {
                        return err
                    }
                }
            }
            break
        }
    }
    
    return nil
}

// Helper to call Overpass API
func (s *server) callOverpass(query string, timeout int32) (*http.Response, error) {
    if timeout == 0 {
        timeout = 180
    }

    req, err := http.NewRequest("POST", s.overpassURL+"/api/interpreter", 
        strings.NewReader(fmt.Sprintf("[timeout:%d][out:json];%s", timeout, query)))
    if err != nil {
        return nil, err
    }

    return s.httpClient.Do(req)
}

// Convert JSON element to protobuf
func convertElement(elem overpassElement) *pb.Element {
    switch elem.Type {
    case "node":
        return &pb.Element{
            Element: &pb.Element_Node{
                Node: &pb.Node{
                    Id:   elem.ID,
                    Lat:  elem.Lat,
                    Lon:  elem.Lon,
                    Tags: elem.Tags,
                },
            },
        }
    case "way":
        return &pb.Element{
            Element: &pb.Element_Way{
                Way: &pb.Way{
                    Id:       elem.ID,
                    NodeRefs: elem.Nodes,
                    Tags:     elem.Tags,
                },
            },
        }
    case "relation":
        var members []*pb.Member
        for _, m := range elem.Members {
            members = append(members, &pb.Member{
                Type: convertMemberType(m.Type),
                Ref:  m.Ref,
                Role: m.Role,
            })
        }
        return &pb.Element{
            Element: &pb.Element_Relation{
                Relation: &pb.Relation{
                    Id:      elem.ID,
                    Members: members,
                    Tags:    elem.Tags,
                },
            },
        }
    }
    return nil
}

// JSON structures for parsing Overpass response
type overpassJSONResponse struct {
    Version   float64 `json:"version"`
    Generator string  `json:"generator"`
    OSM3S     struct {
        Copyright string `json:"copyright"`
    } `json:"osm3s"`
    Elements []overpassElement `json:"elements"`
}

type overpassElement struct {
    Type    string            `json:"type"`
    ID      int64             `json:"id"`
    Lat     float64           `json:"lat"`
    Lon     float64           `json:"lon"`
    Nodes   []int64           `json:"nodes"`
    Members []overpassMember  `json:"members"`
    Tags    map[string]string `json:"tags"`
}

type overpassMember struct {
    Type string `json:"type"`
    Ref  int64  `json:"ref"`
    Role string `json:"role"`
}

func convertMemberType(t string) pb.Member_Type {
    switch t {
    case "node":
        return pb.Member_NODE
    case "way":
        return pb.Member_WAY
    case "relation":
        return pb.Member_RELATION
    }
    return pb.Member_NODE
}

func main() {
    lis, err := net.Listen("tcp", ":50051")
    if err != nil {
        log.Fatalf("failed to listen: %v", err)
    }

    s := grpc.NewServer()
    pb.RegisterOverpassAPIServer(s, &server{
        overpassURL: "http://localhost:8091",
        httpClient: &http.Client{
            Timeout: 5 * time.Minute,
        },
    })

    log.Println("gRPC server listening on :50051")
    if err := s.Serve(lis); err != nil {
        log.Fatalf("failed to serve: %v", err)
    }
}