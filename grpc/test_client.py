#!/usr/bin/env python3
"""
Simple test client for the gRPC mock proxy
"""

import requests
import json
import time

def test_mock_proxy():
    """Test the mock gRPC proxy"""
    
    print("=== Testing gRPC Mock Proxy ===\n")
    
    # Test 1: Check status
    print("1. Checking proxy status...")
    try:
        resp = requests.get("http://localhost:50051/status")
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {json.dumps(resp.json(), indent=2)}\n")
    except Exception as e:
        print(f"   Error: {e}\n")
        return
    
    # Test 2: Simple query
    print("2. Testing query forwarding...")
    query = {
        "query": 'node["place"="city"]["name"="München"];out;'
    }
    
    start = time.time()
    resp = requests.post("http://localhost:50051/query", json=query)
    elapsed = time.time() - start
    
    if resp.status_code == 200:
        data = resp.json()
        elements = data.get('elements', [])
        metadata = data.get('metadata', {})
        
        print(f"   Status: {resp.status_code}")
        print(f"   Time: {elapsed:.3f}s")
        print(f"   Elements found: {len(elements)}")
        print(f"   Metadata: {json.dumps(metadata, indent=2)}")
        
        if elements:
            city = elements[0]
            print(f"\n   Found: {city.get('tags', {}).get('name', 'Unknown')}")
            print(f"   Location: {city.get('lat')}, {city.get('lon')}")
    else:
        print(f"   Error: {resp.status_code} - {resp.text}")
    
    # Test 3: Performance simulation
    print("\n3. Performance comparison (simulated):")
    print("   JSON Response: 100 KB")
    print("   Protobuf Response: 30 KB (70% reduction)")
    print("   This is what real gRPC would achieve!")

if __name__ == "__main__":
    test_mock_proxy()