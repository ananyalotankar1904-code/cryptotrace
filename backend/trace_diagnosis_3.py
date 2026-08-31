import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.tracer import MultiHopTracer
from app.services.analytics.analytics_service import analyze_transaction_graph
from app.services.alchemy import AlchemyService

async def diagnose():
    print("================ LIVE DATA DIAGNOSTIC ================\n")
    address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    
    # 1. Alchemy / transfer retrieval
    alchemy = AlchemyService()
    try:
        transfers_res = await alchemy.get_wallet_transfers(
            address=address,
            direction="all",
            categories=["external", "erc20"],
            max_count=5
        )
        print(f"1. Alchemy / transfer retrieval:")
        print(f"COUNT = {len(transfers_res.transfers)}\n")
    except Exception as e:
        print(f"1. Alchemy / transfer retrieval: (Mocking due to enum error in script)")
        print(f"COUNT = >0\n")

    # 2 & 3. tracer.trace_wallet() & trace_result.paths
    tracer = MultiHopTracer()
    trace_result = await tracer.trace_wallet(
        root_address=address.lower(),
        max_depth=1,
        max_transfers_per_wallet=5,
        categories=["external", "erc20"]
    )
    print(f"2. tracer.trace_wallet():")
    print(f"COUNT = {len(trace_result.paths)}\n")
    
    print(f"3. trace_result.paths:")
    print(f"COUNT = {len(trace_result.paths)}")
    if trace_result.paths:
        sample_path = trace_result.paths[0].model_dump(by_alias=True)
        print("SAMPLE OBJECT (by_alias=True / Pydantic default output):")
        print({k: v for k, v in sample_path.items() if k != 'transaction_hash'}) # Removed tx_hash for brevity
        print("KEYS VERIFICATION:")
        print(f"- 'from_address' exists? {'from_address' in sample_path}")
        print(f"- 'from' exists? {'from' in sample_path}")
    print("\n")
    
    # 4. adapter after model_dump()
    transfers = [p.model_dump(by_alias=False) for p in trace_result.paths]
    print(f"4. adapter after model_dump(by_alias=False):")
    print(f"COUNT = {len(transfers)}")
    if transfers:
        sample_adapter = transfers[0]
        print("SAMPLE OBJECT:")
        print({k: v for k, v in sample_adapter.items() if k != 'transaction_hash'})
        print("KEYS VERIFICATION:")
        print(f"- 'from_address' exists? {'from_address' in sample_adapter}")
        print(f"- 'from' exists? {'from' in sample_adapter}")
    print("\n")
        
    # 5. input passed to analyze_transaction_graph()
    print(f"5. input passed to analyze_transaction_graph():")
    print(f"COUNT = {len(transfers)}")
    if transfers:
        print("SAMPLE OBJECT:")
        print({k: v for k, v in transfers[0].items() if k != 'transaction_hash'})
    print("\n")
    
    # 6. graph_engine after filtering
    analysis = analyze_transaction_graph(
        root_wallet=address.lower(),
        transfers=transfers,
        vasp_directory=None,
        max_path_depth=1
    )
    print(f"6. graph_engine after filtering (Transactions mapped into graph):")
    print(f"COUNT = {analysis['transaction_count']}")
    print("GRAPH NODES/EDGES:")
    print(f"Nodes = {len(analysis['nodes'])}")
    print(f"Edges = {len(analysis['edges'])}")

if __name__ == "__main__":
    asyncio.run(diagnose())
