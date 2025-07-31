#!/usr/bin/env python3
"""
Standalone Overpass Mode Test Script
Tests both HTTP and GRPC modes against a specified Overpass server

Usage:
    python test_overpass_modes_standalone.py [--http-url URL] [--grpc-host HOST] [--grpc-port PORT]

Example:
    python test_overpass_modes_standalone.py --http-url http://localhost:8091/api/interpreter
"""

import argparse
import json
import time
import sys
from typing import Dict, List, Tuple

# Test queries with increasing complexity
TEST_QUERIES = {
    "count_all": {
        "name": "Count all nodes in small area",
        "query": """
[out:json][timeout:25];
node(48.95,10.90,48.96,10.91);
out count;
"""
    },
    "simple_power": {
        "name": "Find power infrastructure",
        "query": """
[out:json][timeout:25];
node["power"](48.95,10.90,48.97,10.92);
out body;
"""
    },
    "substations": {
        "name": "Find substations with voltage",
        "query": """
[out:json][timeout:25];
(
  node["power"="substation"]["voltage"](48.8,10.7,49.1,11.1);
  way["power"="substation"]["voltage"](48.8,10.7,49.1,11.1);
);
out body;
"""
    },
    "high_voltage": {
        "name": "Find high-voltage substations",
        "query": """
[out:json][timeout:25];
(
  node["power"="substation"]["voltage"~"^(110000|220000|380000)$"](48.8,10.7,49.1,11.1);
  way["power"="substation"]["voltage"~"^(110000|220000|380000)$"](48.8,10.7,49.1,11.1);
);
out body;
"""
    },
    "complex_filter": {
        "name": "Complex query with multiple filters",
        "query": """
[out:json][timeout:25];
(
  node["power"="substation"]["voltage"~"^(110000|220000|380000)$"](48.8,10.7,49.1,11.1);
  way["natural"="water"](48.8,10.7,49.1,11.1);
  way["landuse"="forest"](48.8,10.7,49.1,11.1);
  way["landuse"="residential"](48.8,10.7,49.1,11.1);
);
out body;
"""
    }
}


def test_http_mode(url: str) -> Dict:
    """Test HTTP/JSON mode"""
    try:
        import requests
        results = {}
        
        print(f"\n=== Testing HTTP Mode (URL: {url}) ===")
        
        for query_id, query_info in TEST_QUERIES.items():
            print(f"\n{query_info['name']}...")
            
            start_time = time.time()
            response = requests.post(url, data={'data': query_info['query']}, timeout=30)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                elements = data.get('elements', [])
                
                # Count by type
                nodes = sum(1 for e in elements if e.get('type') == 'node')
                ways = sum(1 for e in elements if e.get('type') == 'way')
                relations = sum(1 for e in elements if e.get('type') == 'relation')
                
                # Handle count queries
                if query_id == "count_all":
                    for elem in elements:
                        if elem.get('type') == 'count':
                            total = elem.get('tags', {}).get('total', 0)
                            print(f"  ✓ Count: {total} elements")
                            results[query_id] = {'count': int(total), 'time': elapsed}
                            break
                else:
                    print(f"  ✓ Found: {nodes} nodes, {ways} ways, {relations} relations")
                    print(f"  Time: {elapsed:.3f}s")
                    
                    # Show sample data
                    if elements and query_id in ['substations', 'high_voltage']:
                        print("  Sample results:")
                        for elem in elements[:3]:
                            tags = elem.get('tags', {})
                            name = tags.get('name', 'Unnamed')
                            voltage = tags.get('voltage', 'Unknown')
                            print(f"    - {name}: {voltage}V")
                    
                    results[query_id] = {
                        'nodes': nodes,
                        'ways': ways,
                        'relations': relations,
                        'total': len(elements),
                        'time': elapsed
                    }
            else:
                print(f"  ✗ Error: HTTP {response.status_code}")
                results[query_id] = {'error': response.status_code}
                
        return results
        
    except Exception as e:
        print(f"  ✗ HTTP Error: {e}")
        return {'error': str(e)}


def test_grpc_mode(host: str, port: int) -> Dict:
    """Test GRPC mode"""
    try:
        # Add parent directory to path for imports
        import os
        parent_dir = os.path.dirname(os.path.abspath(__file__))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # Set environment for GRPC mode
        os.environ['OVERPASS_MODE'] = 'grpc'
        os.environ['OVERPASS_GRPC_HOST'] = host
        os.environ['OVERPASS_GRPC_PORT'] = str(port)
        
        from src.core.grpc_overpass_wrapper import GrpcOverpassWrapper
        
        results = {}
        print(f"\n=== Testing GRPC Mode (Host: {host}:{port}) ===")
        
        wrapper = GrpcOverpassWrapper(host=host, port=port)
        
        for query_id, query_info in TEST_QUERIES.items():
            print(f"\n{query_info['name']}...")
            
            start_time = time.time()
            result = wrapper.query(query_info['query'])
            elapsed = time.time() - start_time
            
            nodes = len(result.nodes)
            ways = len(result.ways)
            relations = len(result.relations)
            
            print(f"  ✓ Found: {nodes} nodes, {ways} ways, {relations} relations")
            print(f"  Time: {elapsed:.3f}s")
            
            # Show sample data
            if result.nodes and query_id in ['substations', 'high_voltage']:
                print("  Sample results:")
                for node in list(result.nodes)[:3]:
                    tags = dict(node.tags) if node.tags else {}
                    name = tags.get('name', 'Unnamed')
                    voltage = tags.get('voltage', 'Unknown')
                    print(f"    - {name}: {voltage}V")
            
            results[query_id] = {
                'nodes': nodes,
                'ways': ways,
                'relations': relations,
                'total': nodes + ways + relations,
                'time': elapsed
            }
            
        return results
        
    except Exception as e:
        print(f"  ✗ GRPC Error: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def compare_results(http_results: Dict, grpc_results: Dict):
    """Compare results between modes"""
    print("\n\n=== Comparison ===")
    
    if 'error' in http_results or 'error' in grpc_results:
        print("Cannot compare - one or both modes failed")
        return
    
    print("\n{:<30} {:>15} {:>15} {:>10}".format("Query", "HTTP Results", "GRPC Results", "Match"))
    print("-" * 70)
    
    all_match = True
    
    for query_id, query_info in TEST_QUERIES.items():
        http_res = http_results.get(query_id, {})
        grpc_res = grpc_results.get(query_id, {})
        
        if 'error' in http_res or 'error' in grpc_res:
            print(f"{query_info['name']:<30} {'ERROR':<15} {'ERROR':<15} {'❌':<10}")
            all_match = False
            continue
        
        if query_id == "count_all":
            http_total = http_res.get('count', 0)
            grpc_total = grpc_res.get('total', 0)
        else:
            http_total = http_res.get('total', 0)
            grpc_total = grpc_res.get('total', 0)
        
        match = "✅" if http_total == grpc_total else "❌"
        if http_total != grpc_total:
            all_match = False
            
        print(f"{query_info['name']:<30} {http_total:<15} {grpc_total:<15} {match:<10}")
    
    print("\n" + "=" * 70)
    print(f"Overall result: {'✅ All queries match' if all_match else '❌ Differences detected'}")
    
    # Performance comparison
    print("\n\n=== Performance Comparison ===")
    print("\n{:<30} {:>12} {:>12} {:>10}".format("Query", "HTTP (s)", "GRPC (s)", "Speedup"))
    print("-" * 64)
    
    total_http_time = 0
    total_grpc_time = 0
    
    for query_id, query_info in TEST_QUERIES.items():
        http_res = http_results.get(query_id, {})
        grpc_res = grpc_results.get(query_id, {})
        
        http_time = http_res.get('time', 0)
        grpc_time = grpc_res.get('time', 0)
        
        if http_time > 0 and grpc_time > 0:
            speedup = http_time / grpc_time
            print(f"{query_info['name']:<30} {http_time:>12.3f} {grpc_time:>12.3f} {speedup:>9.1f}x")
            total_http_time += http_time
            total_grpc_time += grpc_time
    
    if total_http_time > 0 and total_grpc_time > 0:
        print("-" * 64)
        total_speedup = total_http_time / total_grpc_time
        print(f"{'Total':<30} {total_http_time:>12.3f} {total_grpc_time:>12.3f} {total_speedup:>9.1f}x")


def main():
    parser = argparse.ArgumentParser(description='Test Overpass API modes (HTTP vs GRPC)')
    parser.add_argument('--http-url', default='http://localhost:8091/api/interpreter',
                        help='HTTP API URL (default: http://localhost:8091/api/interpreter)')
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
    print("=" * 70)
    
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