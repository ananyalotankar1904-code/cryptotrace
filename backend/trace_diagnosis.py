import sys
import os
import json
import asyncio

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.tracer import MultiHopTracer
from app.services.analytics.analytics_service import analyze_transaction_graph

async def diagnose():
    print("--- DIAGNOSIS REPORT ---")
    address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    
    print("\n1 & 2. TRACER OUTPUT")
    tracer = MultiHopTracer()
    trace_result = await tracer.trace_wallet(
        root_address=address.lower(),
        max_depth=1,
        max_transfers_per_wallet=5,
        categories=["external", "erc20"]
    )
    print(f"tracer.trace_wallet() paths count: {len(trace_result.paths)}")
    
    if trace_result.paths:
        print("Raw Tracer Path Object 0 keys/attrs:")
        print(trace_result.paths[0].model_dump().keys())
    
    print("\n3. ADAPTER CONVERSION")
    # This is what's in wallet.py
    transfers = [p.model_dump(by_alias=False) for p in trace_result.paths]
    print(f"Converted transfers list count: {len(transfers)}")
    if transfers:
        print("Adapter transfer dict 0 keys:")
        print(transfers[0].keys())
        
    print("\n4. ANALYTICS INPUT")
    print(f"Passing {len(transfers)} transfers into analyze_transaction_graph")
    
    print("\n5. ANALYTICS EXECUTION")
    try:
        analysis = analyze_transaction_graph(
            root_wallet=address.lower(),
            transfers=transfers,
            vasp_directory=None,
            max_path_depth=1
        )
        print(f"Analytics completed.")
        print(f"Returned transaction_count (from graph): {analysis['transaction_count']}")
        print(f"Returned wallet_count (from graph): {analysis['wallet_count']}")
        print(f"Returned nodes length: {len(analysis['nodes'])}")
        print(f"Returned edges length: {len(analysis['edges'])}")
    except Exception as e:
        print(f"Exception in analytics: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose())
