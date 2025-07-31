// Overpass gRPC Server Implementation
#include <iostream>
#include <memory>
#include <string>
#include <thread>
#include <grpcpp/grpcpp.h>
#include <grpcpp/health_check_service_interface.h>
#include <grpcpp/ext/proto_server_reflection_plugin.h>

#include "overpass.grpc.pb.h"

// For calling existing Overpass API
#include <cstdio>
#include <array>
#include <sstream>

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::ServerWriter;
using grpc::Status;
using overpass::OverpassAPI;
using overpass::QueryRequest;
using overpass::QueryResponse;
using overpass::Element;
using overpass::Node;

class OverpassServiceImpl final : public OverpassAPI::Service {
private:
    // Call existing Overpass interpreter
    std::string executeOverpassQuery(const std::string& query) {
        std::array<char, 128> buffer;
        std::string result;
        
        // Build command to call Overpass interpreter via dispatcher
        std::string cmd = std::string("echo '[out:json];") + query + "' | /opt/overpass/bin/osm3s_query";
        
        // Execute and capture output
        std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.c_str(), "r"), pclose);
        if (!pipe) {
            throw std::runtime_error("popen() failed!");
        }
        
        while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
            result += buffer.data();
        }
        
        return result;
    }
    
    // Parse JSON and convert to protobuf
    void parseJsonToProtobuf(const std::string& json, QueryResponse* response) {
        // In production, use a proper JSON parser like nlohmann/json
        // This is a simplified example
        
        // Extract elements array
        size_t elementsPos = json.find("\"elements\":");
        if (elementsPos == std::string::npos) return;
        
        // Simple node extraction (example)
        size_t nodePos = json.find("\"type\":\"node\"", elementsPos);
        while (nodePos != std::string::npos) {
            auto* element = response->add_elements();
            auto* node = element->mutable_node();
            
            // Extract ID
            size_t idPos = json.find("\"id\":", nodePos);
            if (idPos != std::string::npos) {
                idPos += 5;
                node->set_id(std::stoll(json.substr(idPos)));
            }
            
            // Extract lat/lon
            size_t latPos = json.find("\"lat\":", nodePos);
            if (latPos != std::string::npos) {
                latPos += 6;
                node->set_lat(std::stod(json.substr(latPos)));
            }
            
            size_t lonPos = json.find("\"lon\":", nodePos);
            if (lonPos != std::string::npos) {
                lonPos += 6;
                node->set_lon(std::stod(json.substr(lonPos)));
            }
            
            // Find next node
            nodePos = json.find("\"type\":\"node\"", nodePos + 1);
        }
    }

public:
    Status Query(ServerContext* context, const QueryRequest* request,
                 QueryResponse* response) override {
        try {
            // Execute query through existing Overpass
            std::string jsonResult = executeOverpassQuery(request->query());
            
            // Convert JSON to Protobuf
            parseJsonToProtobuf(jsonResult, response);
            
            // Set metadata
            auto* metadata = response->mutable_metadata();
            metadata->set_generator("Overpass API gRPC");
            metadata->set_copyright("OpenStreetMap contributors");
            
            return Status::OK;
        } catch (const std::exception& e) {
            return Status(grpc::StatusCode::INTERNAL, e.what());
        }
    }
    
    Status StreamQuery(ServerContext* context, const QueryRequest* request,
                      ServerWriter<Element>* writer) override {
        try {
            // Execute query
            std::string jsonResult = executeOverpassQuery(request->query());
            
            // Stream parse and send elements
            // In production, use a streaming JSON parser
            QueryResponse tempResponse;
            parseJsonToProtobuf(jsonResult, &tempResponse);
            
            // Stream each element
            for (const auto& element : tempResponse.elements()) {
                if (!writer->Write(element)) {
                    break;
                }
            }
            
            return Status::OK;
        } catch (const std::exception& e) {
            return Status(grpc::StatusCode::INTERNAL, e.what());
        }
    }
};

void RunServer() {
    std::string server_address("0.0.0.0:50051");
    OverpassServiceImpl service;
    
    grpc::EnableDefaultHealthCheckService(true);
    grpc::reflection::InitProtoReflectionServerBuilderPlugin();
    
    ServerBuilder builder;
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    builder.RegisterService(&service);
    
    // Performance optimizations
    builder.SetMaxReceiveMessageSize(100 * 1024 * 1024); // 100MB
    builder.SetMaxSendMessageSize(100 * 1024 * 1024);    // 100MB
    builder.AddChannelArgument(GRPC_ARG_KEEPALIVE_TIME_MS, 10000);
    builder.AddChannelArgument(GRPC_ARG_KEEPALIVE_TIMEOUT_MS, 5000);
    
    std::unique_ptr<Server> server(builder.BuildAndStart());
    std::cout << "gRPC Server listening on " << server_address << std::endl;
    
    server->Wait();
}

int main(int argc, char** argv) {
    RunServer();
    return 0;
}