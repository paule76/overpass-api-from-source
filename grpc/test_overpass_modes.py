#!/usr/bin/env python3
"""
Standalone Overpass Mode Test Script
Tests both HTTP and GRPC modes against Overpass servers

Usage:
    python test_overpass_modes.py [--http-url URL] [--grpc-host HOST] [--grpc-port PORT]

Example:
    python test_overpass_modes.py --http-url http://localhost:8092/api/interpreter
"""

import argparse
import json
import time
import sys
import os

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test queries with increasing complexity
TEST_QUERIES = {
    "simple_nodes": {
        "name": "Simple node query",
        "query": "node(48.13,11.56,48.14,11.57);out 10;"
    },
    "cafes": {
        "name": "Find cafes",
        "query": 'node["amenity"="cafe"](48.13,11.56,48.15,11.58);out;'
    },
    "power": {
        "name": "Find power infrastructure",
        "query": 'node["power"](48.10,11.50,48.20,11.60);out 20;'
    },
    "restaurants": {
        "name": "Find restaurants and cafes",
        "query": '(node["amenity"="restaurant"](48.13,11.56,48.15,11.58);node["amenity"="cafe"](48.13,11.56,48.15,11.58););out;'
    },
    "highways": {
        "name": "Find highways (limited)",
        "query": 'way["highway"](48.13,11.56,48.14,11.57);out 5;'
    }
}


def test_http_mode(url: str) -> dict:
    """Test HTTP/JSON mode"""
    try:
        import requests
        results = {}
        
        print(f"\n=== Testing HTTP Mode (URL: {url}) ===")
        
        for query_id, query_info in TEST_QUERIES.items():
            print(f"\n{query_info['name']}...")
            
            # Add [out:json] prefix
            full_query = f"[out:json];{query_info['query']}"
            
            start_time = time.time()
            response = requests.post(url, data={'data': full_query}, timeout=30)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                elements = data.get('elements', [])
                
                # Count by type
                nodes = sum(1 for e in elements if e.get('type') == 'node')
                ways = sum(1 for e in elements if e.get('type') == 'way')
                relations = sum(1 for e in elements if e.get('type') == 'relation')
                
                print(f"  ✓ Found: {nodes} nodes, {ways} ways, {relations} relations")
                print(f"  Time: {elapsed:.3f}s")
                print(f"  Data size: {len(response.text):,} bytes")
                
                # Show sample data
                if elements and query_id in ['cafes', 'restaurants']:
                    print("  Sample results:")
                    for elem in elements[:3]:
                        if elem.get('type') == 'node':
                            tags = elem.get('tags', {})
                            name = tags.get('name', 'Unnamed')
                            lat = elem.get('lat', 0)
                            lon = elem.get('lon', 0)
                            print(f"    - {name} at {lat:.6f},{lon:.6f}")
                
                results[query_id] = {
                    'nodes': nodes,
                    'ways': ways,
                    'relations': relations,
                    'total': len(elements),
                    'time': elapsed,
                    'size': len(response.text)
                }
            else:
                print(f"  ✗ Error: HTTP {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                results[query_id] = {'error': response.status_code}
                
        return results
        
    except Exception as e:
        print(f"  ✗ HTTP Error: {e}")
        return {'error': str(e)}


def test_grpc_mode(host: str, port: int) -> dict:
    """Test GRPC mode"""
    try:
        import grpc
        
        # Add client directory to path
        client_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client')
        if client_dir not in sys.path:
            sys.path.insert(0, client_dir)
        
        # Try to import generated files
        try:
            import overpass_pb2
            import overpass_pb2_grpc
        except ImportError:
            print("  ! Generating protobuf files...")
            os.system("python -m grpc_tools.protoc -I. --python_out=client --grpc_python_out=client overpass.proto")
            import overpass_pb2
            import overpass_pb2_grpc
        
        results = {}
        print(f"\n=== Testing GRPC Mode (Host: {host}:{port}) ===")
        
        # Create channel and stub
        channel = grpc.insecure_channel(f'{host}:{port}')
        stub = overpass_pb2_grpc.OverpassAPIStub(channel)
        
        for query_id, query_info in TEST_QUERIES.items():
            print(f"\n{query_info['name']}...")
            
            try:
                start_time = time.time()
                request = overpass_pb2.QueryRequest(query=query_info['query'])
                response = stub.Query(request, timeout=30)
                elapsed = time.time() - start_time
                
                # Count elements
                nodes = sum(1 for e in response.elements if e.HasField('node'))
                ways = sum(1 for e in response.elements if e.HasField('way'))
                relations = sum(1 for e in response.elements if e.HasField('relation'))
                
                print(f"  ✓ Found: {nodes} nodes, {ways} ways, {relations} relations")
                print(f"  Time: {elapsed:.3f}s")
                print(f"  Data size: ~{response.ByteSize():,} bytes (protobuf)")
                
                # Show sample data
                if response.elements and query_id in ['cafes', 'restaurants']:
                    print("  Sample results:")
                    count = 0
                    for elem in response.elements:
                        if elem.HasField('node') and count < 3:
                            node = elem.node
                            name = dict(node.tags).get('name', 'Unnamed') if node.tags else 'Unnamed'
                            print(f"    - {name} at {node.lat:.6f},{node.lon:.6f}")
                            count += 1
                
                results[query_id] = {
                    'nodes': nodes,
                    'ways': ways,
                    'relations': relations,
                    'total': len(response.elements),
                    'time': elapsed,
                    'size': response.ByteSize()
                }
                
            except grpc.RpcError as e:
                print(f"  ✗ GRPC Error: {e.code()}: {e.details()}")
                results[query_id] = {'error': str(e.code())}
            
        return results
        
    except Exception as e:
        print(f"  ✗ GRPC Setup Error: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def compare_results(http_results: dict, grpc_results: dict):
    """Compare results between modes"""
    print("\n\n=== Result Comparison ===")
    
    if 'error' in http_results or 'error' in grpc_results:
        print("Cannot compare - one or both modes failed")
        return
    
    print("\n{:<25} {:>12} {:>12} {:>10}".format("Query", "HTTP Total", "GRPC Total", "Match"))
    print("-" * 60)
    
    all_match = True
    
    for query_id, query_info in TEST_QUERIES.items():
        http_res = http_results.get(query_id, {})
        grpc_res = grpc_results.get(query_id, {})
        
        if 'error' in http_res or 'error' in grpc_res:
            print(f"{query_info['name']:<25} {'ERROR':<12} {'ERROR':<12} {'❌':<10}")
            all_match = False
            continue
        
        http_total = http_res.get('total', 0)
        grpc_total = grpc_res.get('total', 0)
        
        match = "✅" if http_total == grpc_total else "❌"
        if http_total != grpc_total:
            all_match = False
            
        print(f"{query_info['name']:<25} {http_total:>12} {grpc_total:>12} {match:>10}")
    
    print("\n" + "=" * 60)
    print(f"Overall: {'✅ All queries match' if all_match else '❌ Differences detected'}")
    
    # Performance comparison
    print("\n\n=== Performance Comparison ===")
    print("\n{:<25} {:>10} {:>10} {:>10} {:>12} {:>12} {:>10}".format(
        "Query", "HTTP (s)", "GRPC (s)", "Speedup", "HTTP Size", "GRPC Size", "Reduction"))
    print("-" * 100)
    
    total_http_time = 0
    total_grpc_time = 0
    total_http_size = 0
    total_grpc_size = 0
    
    for query_id, query_info in TEST_QUERIES.items():
        http_res = http_results.get(query_id, {})
        grpc_res = grpc_results.get(query_id, {})
        
        if 'error' not in http_res and 'error' not in grpc_res:
            http_time = http_res.get('time', 0)
            grpc_time = grpc_res.get('time', 0)
            http_size = http_res.get('size', 0)
            grpc_size = grpc_res.get('size', 0)
            
            if http_time > 0 and grpc_time > 0:
                speedup = http_time / grpc_time
                reduction = (1 - grpc_size/http_size) * 100 if http_size > 0 else 0
                
                print(f"{query_info['name']:<25} {http_time:>10.3f} {grpc_time:>10.3f} "
                      f"{speedup:>9.1f}x {http_size:>12,} {grpc_size:>12,} {reduction:>9.1f}%")
                
                total_http_time += http_time
                total_grpc_time += grpc_time
                total_http_size += http_size
                total_grpc_size += grpc_size
    
    if total_http_time > 0 and total_grpc_time > 0:
        print("-" * 100)
        total_speedup = total_http_time / total_grpc_time
        total_reduction = (1 - total_grpc_size/total_http_size) * 100 if total_http_size > 0 else 0
        print(f"{'Total':<25} {total_http_time:>10.3f} {total_grpc_time:>10.3f} "
              f"{total_speedup:>9.1f}x {total_http_size:>12,} {total_grpc_size:>12,} {total_reduction:>9.1f}%")


def main():
    parser = argparse.ArgumentParser(description='Test Overpass API modes (HTTP vs GRPC)')
    parser.add_argument('--http-url', default='http://localhost:8092/api/interpreter',
                        help='HTTP API URL (default: http://localhost:8092/api/interpreter)')
    parser.add_argument('--grpc-host', default='localhost',
                        help='GRPC host (default: localhost)')
    parser.add_argument('--grpc-port', type=int, default=50051,
                        help='GRPC port (default: 50051)')
    parser.add_argument('--skip-http', action='store_true',
                        help='Skip HTTP tests')
    parser.add_argument('--skip-grpc', action='store_true',
                        help='Skip GRPC tests')
    
    args = parser.parse_args()
    
    print("Overpass Mode Comparison Test")
    print("=" * 60)
    
    # Check if grpcio is installed
    if not args.skip_grpc:
        try:
            import grpc
        except ImportError:
            print("\n⚠️  grpcio not installed. Install with: pip install grpcio grpcio-tools")
            args.skip_grpc = True
    
    # Test HTTP mode
    http_results = {}
    if not args.skip_http:
        http_results = test_http_mode(args.http_url)
    else:
        print("\n(HTTP tests skipped)")
    
    # Test GRPC mode
    grpc_results = {}
    if not args.skip_grpc:
        grpc_results = test_grpc_mode(args.grpc_host, args.grpc_port)
    else:
        print("\n(GRPC tests skipped)")
    
    # Compare results
    if not args.skip_http and not args.skip_grpc:
        compare_results(http_results, grpc_results)
    
    # Save results to file
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'config': {
            'http_url': args.http_url,
            'grpc_host': args.grpc_host,
            'grpc_port': args.grpc_port
        },
        'http_results': http_results,
        'grpc_results': grpc_results
    }
    
    output_file = f"overpass_test_results_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")


if __name__ == '__main__':
    main()