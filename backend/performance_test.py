#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Performance testing script
"""

import time
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

class PerformanceTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = []
    
    def test_endpoint(self, method, endpoint, data=None, num_requests=100):
        """Test endpoint performance"""
        print(f"\nTesting {method} {endpoint}")
        print(f"Requests: {num_requests}")
        
        times = []
        errors = 0
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for _ in range(num_requests):
                if method == "GET":
                    future = executor.submit(self._get_request, endpoint)
                elif method == "POST":
                    future = executor.submit(self._post_request, endpoint, data)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    elapsed = future.result()
                    if elapsed:
                        times.append(elapsed)
                except Exception as e:
                    errors += 1
                    print(f"Error: {e}")
        
        # Calculate statistics
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            p95_time = sorted(times)[int(len(times) * 0.95)]
            p99_time = sorted(times)[int(len(times) * 0.99)]
            
            print(f"\nResults:")
            print(f"  Average: {avg_time*1000:.2f}ms")
            print(f"  Min: {min_time*1000:.2f}ms")
            print(f"  Max: {max_time*1000:.2f}ms")
            print(f"  P95: {p95_time*1000:.2f}ms")
            print(f"  P99: {p99_time*1000:.2f}ms")
            print(f"  Errors: {errors}")
            print(f"  Success Rate: {(num_requests-errors)/num_requests*100:.1f}%")
            
            return {
                'endpoint': endpoint,
                'avg': avg_time,
                'min': min_time,
                'max': max_time,
                'p95': p95_time,
                'p99': p99_time,
                'errors': errors
            }
    
    def _get_request(self, endpoint):
        """Make GET request and measure time"""
        start = time.time()
        try:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            response.raise_for_status()
            return time.time() - start
        except Exception as e:
            raise e
    
    def _post_request(self, endpoint, data):
        """Make POST request and measure time"""
        start = time.time()
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return time.time() - start
        except Exception as e:
            raise e
    
    def run_suite(self):
        """Run full test suite"""
        print("="*50)
        print("AAIS Performance Test Suite")
        print("="*50)
        
        # Test health endpoint
        self.test_endpoint("GET", "/health", num_requests=100)
        
        # Test text generation
        self.test_endpoint(
            "POST",
            "/api/text/generate",
            data={
                "prompt": "Write a story",
                "max_length": 512,
                "temperature": 0.7
            },
            num_requests=10
        )
        
        # Test batch processing
        self.test_endpoint(
            "POST",
            "/api/batch/text-generate",
            data={
                "prompts": ["Prompt 1", "Prompt 2", "Prompt 3"],
                "max_length": 512
            },
            num_requests=5
        )
        
        print("\n" + "="*50)
        print("Test Suite Complete")
        print("="*50)

if __name__ == "__main__":
    tester = PerformanceTester()
    tester.run_suite()
