import requests

r = requests.get('http://127.0.0.1:8000/wallet/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045/analyze?max_depth=1&max_transfers_per_wallet=5')
data = r.json()

print(f"Transactions analyzed: {data.get('summary', {}).get('transactions_analyzed')}")
print(f"Wallets discovered: {data.get('summary', {}).get('wallets_discovered')}")
print(f"Nodes length: {len(data.get('graph', {}).get('nodes', []))}")
print(f"Edges length: {len(data.get('graph', {}).get('edges', []))}")
print(f"Risk Score: {data.get('risk_analysis', {}).get('risk_score')}")
