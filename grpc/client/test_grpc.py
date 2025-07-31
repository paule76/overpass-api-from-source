#!/usr/bin/env python3
"""
Test gRPC Overpass API Client
"""

import grpc
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import generated protobuf classes
import overpass_pb2
import overpass_pb2_grpc


def test_simple_query():
    """Test a simple Overpass query via gRPC"""
    # Connect to server
    channel = grpc.insecure_channel('localhost:50051')
    stub = overpass_pb2_grpc.OverpassAPIStub(channel)
    
    # Simple query for nodes
    query = 'node(48.13,11.56,48.14,11.57);out 10;'
    
    print("Testing gRPC Overpass API...")
    print(f"Query: {query}")
    
    try:
        # Make request
        request = overpass_pb2.QueryRequest(query=query)
        response = stub.Query(request)
        
        print(f"\nReceived {len(response.elements)} elements")
        print(f"Metadata: {response.metadata.generator}")
        
        # Show first few nodes
        for i, element in enumerate(response.elements[:5]):
            if element.HasField('node'):
                node = element.node
                print(f"Node {i+1}: ID={node.id}, lat={node.lat:.6f}, lon={node.lon:.6f}")
                
    except grpc.RpcError as e:
        print(f"gRPC Error: {e.status()}: {e.details()}")
        return False
        
    return True


def test_streaming_query():
    """Test streaming query"""
    channel = grpc.insecure_channel('localhost:50051')
    stub = overpass_pb2_grpc.OverpassAPIStub(channel)
    
    # Query for amenities
    query = 'node["amenity"="cafe"](48.13,11.56,48.14,11.57);out;'
    
    print("\n\nTesting streaming query...")
    print(f"Query: {query}")
    
    try:
        request = overpass_pb2.QueryRequest(query=query)
        stream = stub.StreamQuery(request)
        
        count = 0
        for element in stream:
            count += 1
            if count <= 3 and element.HasField('node'):
                node = element.node
                print(f"Streamed Node {count}: ID={node.id}")
                
        print(f"Total streamed elements: {count}")
        
    except grpc.RpcError as e:
        print(f"gRPC Error: {e.status()}: {e.details()}")
        return False
        
    return True


if __name__ == "__main__":
    print("=== gRPC Overpass API Test ===\n")
    
    # Test basic query
    if test_simple_query():
        print("\n✓ Basic query test passed")
    else:
        print("\n✗ Basic query test failed")
        
    # Test streaming
    if test_streaming_query():
        print("\n✓ Streaming query test passed")
    else:
        print("\n✗ Streaming query test failed")