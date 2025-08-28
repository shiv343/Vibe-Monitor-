import time
import requests
import random
import threading
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8000"
ENDPOINTS = ["/hello", "/slow", "/error", "/"]

def make_request(endpoint_url, request_id):
    """Make a single request"""
    try:
        response = requests.get(endpoint_url, timeout=10)
        print(f"Request {request_id}: {response.status_code} - {endpoint_url}")
        if response.status_code == 200:
            data = response.json()
            if 'delay_seconds' in data:
                print(f"  └─ Delay: {data['delay_seconds']}s")
        return response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Request {request_id}: ERROR - {endpoint_url} - {e}")
        return None

def generate_traffic():
    """Generate realistic traffic patterns"""
    print("🚦 Starting traffic generation...")
    print("📊 Endpoints being tested:", ENDPOINTS)
    print("-" * 50)
    
    request_count = 0
    
    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            for i in range(200):  
                # Randomly select endpoint with different weights
                weights = [0.6, 0.1, 0.05, 0.25]  # hello, slow, error, root
                endpoint = random.choices(ENDPOINTS, weights=weights)[0]
                url = f"{BASE_URL}{endpoint}"
                
                # Submit request to thread pool
                future = executor.submit(make_request, url, i + 1)
                request_count += 1
                
               
                delay = random.uniform(0.05, 0.5)
                time.sleep(delay)
                
                # Every 50 requests, print status
                if (i + 1) % 50 == 0:
                    print(f" Sent {i + 1} requests...")
                    
    except KeyboardInterrupt:
        print("\n  Traffic generation stopped by user")
    
    print(f"\n Traffic generation completed! Total requests: {request_count}")
    print("Check Grafana at http://localhost:3000 for metrics, logs, and traces")

if __name__ == "__main__":
    # Wait a bit for services to be ready
    print(" Waiting 5 seconds for services to start...")
    time.sleep(5)
    
    # Test connectivity first
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f" Service is ready! Health check: {response.status_code}")
    except Exception as e:
        print(f" Service not ready: {e}")
        print("Make sure to run 'docker-compose up' first")
        exit(1)
    
    generate_traffic()
