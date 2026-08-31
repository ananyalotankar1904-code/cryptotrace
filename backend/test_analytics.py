import sys
import os
import json
import asyncio

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.analytics.analytics_service import analyze_transaction_graph
from app.services.tracer import MultiHopTracer

async def main():
    address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    tracer = MultiHopTracer()
    
    print("Running tracer...")
    trace_result = await tracer.trace_wallet(
        root_address=address.lower(),
        max_depth=1,
        max_transfers_per_wallet=5,
        categories=["external", "erc20"]
    )
    
    transfers = [p.model_dump(by_alias=False) for p in trace_result.paths]
    print(f"Tracer returned {len(transfers)} transfers.")
    
    if transfers:
        print("First transfer structure:")
        print(transfers[0])
        
    print("\nRunning analytics...")
    analysis = analyze_transaction_graph(
        root_wallet=address.lower(),
        transfers=transfers,
        vasp_directory=None,
        max_path_depth=1
    )
    
    print(f"Transactions analyzed: {analysis['transaction_count']}")
    print(f"Wallets discovered: {analysis['wallet_count']}")
    print(f"Nodes length: {len(analysis['nodes'])}")
    print(f"Edges length: {len(analysis['edges'])}")
    print(f"Risk Score: {analysis['risk_score']}")
    print(f"Risk Indicators: {analysis['risk_indicators']}")

if __name__ == "__main__":
    asyncio.run(main())
