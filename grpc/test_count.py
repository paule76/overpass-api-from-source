#!/usr/bin/env python3
"""
Test Count Queries in gRPC vs HTTP
"""

import requests
import grpc
import sys
import os

# Add client directory to path
sys.path.append('client')
import overpass_pb2
import overpass_pb2_grpc

def test_count_http():
    print("=== HTTP Count Test ===")
    query = "[out:json];node(48.13,11.56,48.15,11.58);out count;"
    
    response = requests.post('http://localhost:8092/api/interpreter', 
                           data={'data': query}, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        elements = data.get('elements', [])
        if elements and elements[0].get('type') == 'count':
            count_elem = elements[0]
            tags = count_elem.get('tags', {})
            print(f"✓ HTTP Count: {tags.get('total', 0)} total")
            print(f"  - Nodes: {tags.get('nodes', 0)}")
            print(f"  - Ways: {tags.get('ways', 0)}")
            print(f"  - Relations: {tags.get('relations', 0)}")
            return tags
    
    print("✗ HTTP Count failed")
    return None

def test_count_grpc():
    print("\n=== gRPC Count Test ===")
    
    channel = grpc.insecure_channel('localhost:50051')
    stub = overpass_pb2_grpc.OverpassAPIStub(channel)
    
    query = "node(48.13,11.56,48.15,11.58);out count;"
    request = overpass_pb2.QueryRequest(query=query)
    
    try:
        response = stub.Query(request, timeout=30)
        
        count_elements = []
        for element in response.elements:
            if element.HasField('node'):
                node = element.node
                tags = dict(node.tags)
                if tags.get('_type') == 'count':
                    count_elements.append(tags)
        
        if count_elements:
            count_data = count_elements[0]
            print(f"✓ gRPC Count: {count_data.get('total', 0)} total")
            print(f"  - Nodes: {count_data.get('nodes', 0)}")
            print(f"  - Ways: {count_data.get('ways', 0)}")
            print(f"  - Relations: {count_data.get('relations', 0)}")
            return count_data
        else:
            print("✗ No count elements found in gRPC response")
            return None
            
    except grpc.RpcError as e:
        print(f"✗ gRPC Error: {e}")
        return None

def main():
    print("Count Query Test\n")
    
    http_result = test_count_http()
    grpc_result = test_count_grpc()
    
    if http_result and grpc_result:
        http_total = int(http_result.get('total', 0))
        grpc_total = int(grpc_result.get('total', 0))
        
        print(f"\n=== Comparison ===")
        print(f"HTTP total: {http_total}")
        print(f"gRPC total: {grpc_total}")
        
        if http_total == grpc_total:
            print("✅ Count queries match!")
        else:
            print("❌ Count queries don't match")
    else:
        print("\n❌ One or both tests failed")

if __name__ == "__main__":
    main()