// Overpass gRPC Server Implementation
#include <iostream>
#include <memory>
#include <string>
#include <thread>
#include <grpcpp/grpcpp.h>
#include <grpcpp/health_check_service_interface.h>
#include <grpcpp/ext/proto_server_reflection_plugin.h>
#include <nlohmann/json.hpp>

#include "overpass.grpc.pb.h"

// For calling existing Overpass API
#include <cstdio>
#include <array>
#include <sstream>

using json = nlohmann::json;

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
    void parseJsonToProtobuf(const std::string& jsonStr, QueryResponse* response) {
        try {
            json j = json::parse(jsonStr);
            
            // Parse metadata
            if (j.contains("osm3s")) {
                auto* metadata = response->mutable_metadata();
                metadata->set_generator(j.value("generator", "Overpass API"));
                if (j["osm3s"].contains("copyright")) {
                    metadata->set_copyright(j["osm3s"]["copyright"]);
                }
            }
            
            // Parse elements
            if (j.contains("elements")) {
                for (const auto& elem : j["elements"]) {
                    auto* element = response->add_elements();
                    std::string type = elem.value("type", "");
                    
                    if (type == "node") {
                        auto* node = element->mutable_node();
                        node->set_id(elem.value("id", 0));
                        node->set_lat(elem.value("lat", 0.0));
                        node->set_lon(elem.value("lon", 0.0));
                        
                        // Parse tags
                        if (elem.contains("tags")) {
                            for (auto& [key, value] : elem["tags"].items()) {
                                (*node->mutable_tags())[key] = value.get<std::string>();
                            }
                        }
                    }
                    else if (type == "way") {
                        auto* way = element->mutable_way();
                        way->set_id(elem.value("id", 0));
                        
                        // Parse node refs
                        if (elem.contains("nodes")) {
                            for (const auto& nodeRef : elem["nodes"]) {
                                way->add_node_refs(nodeRef.get<int64_t>());
                            }
                        }
                        
                        // Parse tags
                        if (elem.contains("tags")) {
                            for (auto& [key, value] : elem["tags"].items()) {
                                (*way->mutable_tags())[key] = value.get<std::string>();
                            }
                        }
                    }
                    else if (type == "relation") {
                        auto* relation = element->mutable_relation();
                        relation->set_id(elem.value("id", 0));
                        
                        // Parse members
                        if (elem.contains("members")) {
                            for (const auto& memberJson : elem["members"]) {
                                auto* member = relation->add_members();
                                member->set_ref(memberJson.value("ref", 0));
                                member->set_role(memberJson.value("role", ""));
                                
                                std::string memberType = memberJson.value("type", "");
                                if (memberType == "node") {
                                    member->set_type(overpass::Member::NODE);
                                } else if (memberType == "way") {
                                    member->set_type(overpass::Member::WAY);
                                } else if (memberType == "relation") {
                                    member->set_type(overpass::Member::RELATION);
                                }
                            }
                        }
                        
                        // Parse tags
                        if (elem.contains("tags")) {
                            for (auto& [key, value] : elem["tags"].items()) {
                                (*relation->mutable_tags())[key] = value.get<std::string>();
                            }
                        }
                    }
                }
            }
        } catch (const std::exception& e) {
            std::cerr << "JSON parsing error: " << e.what() << std::endl;
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