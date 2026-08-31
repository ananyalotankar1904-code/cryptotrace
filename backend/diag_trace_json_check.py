"""
TARGETED DIAGNOSTIC — verifies what happens when /trace JSON response
(with 'from'/'to' aliased keys) is fed into the graph_engine.
This simulates what happens if a client POSTs trace_output.json to /analyze,
OR if the server re-serializes TracePathItem with by_alias=True before analytics.
"""
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.services.analytics.graph_engine import BlockchainGraphBuilder

# Load the real saved trace output (serialized by the /trace endpoint → by_alias=True → "from"/"to")
with open("trace_output.json", "r") as f:
    trace_data = json.load(f)

paths = trace_data["paths"]
root  = trace_data["root_wallet"]

print(f"trace_output.json paths count : {len(paths)}")
print(f"Sample keys in paths[0]       : {list(paths[0].keys())}")
print(f"  'from_address' present: {'from_address' in paths[0]}")
print(f"  'from'         present: {'from' in paths[0]}")
print(f"  'to_address'   present: {'to_address' in paths[0]}")
print(f"  'to'           present: {'to' in paths[0]}")

# Simulate graph_engine filter exactly as it appears in source
skip = sum(1 for tx in paths if not str(tx.get("from_address","")).lower() or not str(tx.get("to_address","")).lower())
print(f"\nRecords skipped by graph_engine (from_address/to_address lookup): {skip}/{len(paths)}")

builder = BlockchainGraphBuilder()
graph = builder.build_transaction_graph(paths, root_wallet=root)
print(f"graph.number_of_edges() = {graph.number_of_edges()}")
print(f"graph.number_of_nodes() = {graph.number_of_nodes()}")

# Now check: what does model_dump(by_alias=True) produce vs by_alias=False
import asyncio
from app.services.tracer import MultiHopTracer

async def check_serialization():
    tracer = MultiHopTracer()
    trace_result = await tracer.trace_wallet(
        root_address=root,
        max_depth=2,
        max_transfers_per_wallet=5,
        categories=["external","erc20"],
    )
    if not trace_result.paths:
        print("\nNo paths returned for this wallet.")
        return

    p = trace_result.paths[0]
    dump_false = p.model_dump(by_alias=False)
    dump_true  = p.model_dump(by_alias=True)
    print(f"\nmodel_dump(by_alias=False) keys: {list(dump_false.keys())[:5]}")
    print(f"model_dump(by_alias=True)  keys: {list(dump_true.keys())[:5]}")
    print(f"\n'from_address' in dump_false: {'from_address' in dump_false}")
    print(f"'from'         in dump_false: {'from' in dump_false}")
    print(f"'from_address' in dump_true : {'from_address' in dump_true}")
    print(f"'from'         in dump_true : {'from' in dump_true}")

asyncio.run(check_serialization())
