import asyncio
import os
import sys

# Add the current directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

# Create test client
client = TestClient(app)

print("Starting test...")
# Test the new analyze endpoint using a known test address (e.g., vitalik.eth)
address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
response = client.get(f"/wallet/{address}/analyze?max_depth=1&max_transfers_per_wallet=5")

print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Risk Score: {data.get('risk_analysis', {}).get('risk_score')}")
    print(f"Nodes: {len(data.get('graph', {}).get('nodes', []))}")
    print(f"Edges: {len(data.get('graph', {}).get('edges', []))}")
    print("SUCCESS!")
else:
    print(f"Error Response: {response.text}")
    print("FAILED!")
