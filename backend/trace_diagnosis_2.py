import sys
import os
import json
import asyncio

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.tracer import MultiHopTracer
from app.services.analytics.analytics_service import analyze_transaction_graph
from app.services.alchemy import AlchemyService

async def diagnose():
    print("--- LIVE DIAGNOSTIC TRACE ---")
    address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    
    # 1. /transfers response count
    print("\n1. /TRANSFERS RAW OUTPUT COUNT")
    alchemy = AlchemyService()
    try:
        transfers_res = await alchemy.get_wallet_transfers(
            address=address,
            direction="all",
            categories=["external", "erc20"],
            max_count=5
        )
        print(f"Alchemy /transfers count: {len(transfers_res.transfers)}")
        if transfers_res.transfers:
            print("First raw transfer keys:")
            print(transfers_res.transfers[0].model_dump().keys())
    except Exception as e:
        print(f"Alchemy API error (ignoring for trace): {e}")

    # 2. trace_wallet() output count
    print("\n2. TRACER OUTPUT COUNT")
    tracer = MultiHopTracer()
    trace_result = await tracer.trace_wallet(
        root_address=address.lower(),
        max_depth=1,
        max_transfers_per_wallet=5,
        categories=["external", "erc20"]
    )
    print(f"trace_wallet() paths count: {len(trace_result.paths)}")
    if trace_result.paths:
        print("First tracer path object structure (aliases active):")
        print(trace_result.paths[0].model_dump(by_alias=True).keys())
    
    # 3. adapter output count
    print("\n3. ADAPTER OUTPUT COUNT")
    # This simulates the current fix in wallet.py
    transfers = [p.model_dump(by_alias=False) for p in trace_result.paths]
    print(f"Converted transfers list count: {len(transfers)}")
    if transfers:
        print("First adapter transfer dict keys:")
        print(transfers[0].keys())
        
    # 4. analyze_transaction_graph() input count
    print("\n4. ANALYTICS INPUT COUNT")
    print(f"Passing {len(transfers)} transfers into analyze_transaction_graph")
    
    # 5. graph nodes/edges generated
    print("\n5. GRAPH NODES/EDGES GENERATED")
    try:
        analysis = analyze_transaction_graph(
            root_wallet=address.lower(),
            transfers=transfers,
            vasp_directory=None,
            max_path_depth=1
        )
        print(f"Graph generation successful.")
        print(f"Nodes generated: {len(analysis['nodes'])}")
        print(f"Edges generated: {len(analysis['edges'])}")
        print(f"Transactions Analyzed inside graph: {analysis['transaction_count']}")
    except Exception as e:
        print(f"Exception in analytics: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose())
