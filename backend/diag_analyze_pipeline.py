"""
DIAGNOSTIC SCRIPT — /analyze pipeline count tracer
====================================================
Traces transaction COUNT at every stage:
  Stage 1 : Alchemy transfer retrieval
  Stage 2 : tracer.trace_wallet()
  Stage 3 : trace_result.paths
  Stage 4 : after model_dump(by_alias=False)
  Stage 5 : input passed to analyze_transaction_graph()
  Stage 6 : graph_engine after filtering (build_transaction_graph)

For stages 3-6 also prints ONE sample object + key audit.

DO NOT modify production code — read-only diagnostic.
"""

import asyncio
import sys
import os
import json

# ── Make sure we can import from the backend app ─────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.alchemy import AlchemyService
from app.services.tracer import MultiHopTracer
from app.models.transfer import TransferDirection
from app.services.analytics.graph_engine import BlockchainGraphBuilder

# ── CONFIG — change this to the wallet that works in /transfers ───────────────
TARGET_WALLET = "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae"  # replace if needed
MAX_DEPTH = 3
MAX_TRANSFERS = 25
CATEGORIES = ["external", "erc20"]

SEPARATOR = "\n" + "=" * 70 + "\n"

def print_key_audit(sample: dict, label: str):
    """Check which key variants are present and print a key audit."""
    print(f"\n  -- Key Audit for {label} --")
    keys_to_check = [
        ("from_address", "from"),
        ("to_address", "to"),
        ("transaction_hash",),
        ("asset",),
        ("value",),
        ("timestamp",),
        ("hop",),
    ]
    actual_keys = set(sample.keys())
    for variants in keys_to_check:
        found = [k for k in variants if k in actual_keys]
        missing = [k for k in variants if k not in actual_keys]
        status = "PRESENT" if found else "MISSING"
        found_str = ", ".join(f'"{k}"' for k in found) if found else "none"
        miss_str  = ", ".join(f'"{k}"' for k in missing) if missing else "none"
        print(f"    [{status}]  found={found_str}  missing={miss_str}")


def safe_sample(obj):
    """Return a truncated representation safe to print."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in ("transaction_hash", "from_address", "from", "to_address", "to",
                     "asset", "value", "timestamp", "hop", "block_number", "category"):
                if isinstance(v, str) and len(v) > 20:
                    out[k] = v[:10] + "..." + v[-6:]   # truncate long hashes
                else:
                    out[k] = v
        return out
    return str(obj)[:200]


async def run_diagnostic():
    print(SEPARATOR)
    print("  DIAGNOSTIC: /analyze pipeline -- count tracer")
    print(f"  Target wallet : {TARGET_WALLET}")
    print(f"  max_depth={MAX_DEPTH}  max_transfers={MAX_TRANSFERS}")
    print(SEPARATOR)

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 1 — Alchemy transfer retrieval (direct, same as /transfers)
    # ─────────────────────────────────────────────────────────────────────────
    print("STAGE 1 -- Alchemy / transfer retrieval (TransferDirection.FROM)")
    alchemy = AlchemyService()
    try:
        transfer_response = await alchemy.get_wallet_transfers(
            address=TARGET_WALLET,
            direction=TransferDirection.FROM,
            categories=CATEGORIES,
            max_count=MAX_TRANSFERS,
        )
        stage1_count = len(transfer_response.transfers)
        print(f"  COUNT = {stage1_count}")
        print(f"  transfer_response.transfer_count field = {transfer_response.transfer_count}")
        if stage1_count > 0:
            sample = transfer_response.transfers[0]
            print(f"  Sample TransferItem (type={type(sample).__name__}):")
            print(f"    from_address = {getattr(sample, 'from_address', 'MISSING')!r}")
            print(f"    to_address   = {getattr(sample, 'to_address', 'MISSING')!r}")
    except Exception as exc:
        print(f"  ERROR: {exc}")
        stage1_count = 0
    print()

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 2 — tracer.trace_wallet()
    # ─────────────────────────────────────────────────────────────────────────
    print("STAGE 2 -- tracer.trace_wallet()")
    tracer = MultiHopTracer()
    try:
        trace_result = await tracer.trace_wallet(
            root_address=TARGET_WALLET,
            max_depth=MAX_DEPTH,
            max_transfers_per_wallet=MAX_TRANSFERS,
            categories=CATEGORIES,
        )
        stage2_count = trace_result.summary.transfers_analyzed
        stage2_paths_len = len(trace_result.paths)
        print(f"  COUNT (summary.transfers_analyzed) = {stage2_count}")
        print(f"  COUNT (len(trace_result.paths))    = {stage2_paths_len}")
        print(f"  summary.wallets_queried = {trace_result.summary.wallets_queried}")
        print(f"  summary.max_hop_reached = {trace_result.summary.max_hop_reached}")
        print(f"  warnings: {trace_result.summary.warnings[:3]}")
    except Exception as exc:
        print(f"  ERROR: {exc}")
        import traceback; traceback.print_exc()
        return
    print()

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 3 — trace_result.paths  (raw Pydantic objects)
    # ─────────────────────────────────────────────────────────────────────────
    print("STAGE 3 -- trace_result.paths  (raw TracePathItem Pydantic objects)")
    stage3_count = len(trace_result.paths)
    print(f"  COUNT = {stage3_count}")
    if stage3_count > 0:
        sample_obj = trace_result.paths[0]
        print(f"  Sample TracePathItem model_fields: {list(sample_obj.model_fields.keys())}")
        print(f"    .from_address     = {getattr(sample_obj, 'from_address', 'MISSING')!r}")
        print(f"    .to_address       = {getattr(sample_obj, 'to_address',   'MISSING')!r}")
        tx_hash = getattr(sample_obj, 'transaction_hash', 'MISSING')
        print(f"    .transaction_hash = {str(tx_hash)[:14]}... (truncated)")
        print(f"    .asset     = {getattr(sample_obj, 'asset',     'MISSING')!r}")
        print(f"    .value     = {getattr(sample_obj, 'value',     'MISSING')!r}")
        print(f"    .timestamp = {getattr(sample_obj, 'timestamp', 'MISSING')!r}")
        print(f"    .hop       = {getattr(sample_obj, 'hop',       'MISSING')!r}")
    print()

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 4 — after model_dump(by_alias=False)   <- EXACTLY what /analyze does
    # ─────────────────────────────────────────────────────────────────────────
    print("STAGE 4 -- model_dump(by_alias=False)  [same call as /analyze route]")
    transfers_no_alias = [p.model_dump(by_alias=False) for p in trace_result.paths]
    stage4_count = len(transfers_no_alias)
    print(f"  COUNT = {stage4_count}")
    if stage4_count > 0:
        sample_d = transfers_no_alias[0]
        print(f"  Sample dict keys: {list(sample_d.keys())}")
        print(f"  Sample (redacted):")
        print(f"    {json.dumps(safe_sample(sample_d), indent=4)}")
        print_key_audit(sample_d, "model_dump(by_alias=False)")
    print()

    # -- Also show what model_dump(by_alias=True) produces for comparison -----
    print("STAGE 4b -- model_dump(by_alias=True)  [alias mode, for comparison]")
    transfers_with_alias = [p.model_dump(by_alias=True) for p in trace_result.paths]
    if transfers_with_alias:
        sample_alias = transfers_with_alias[0]
        print(f"  Sample dict keys: {list(sample_alias.keys())}")
        print_key_audit(sample_alias, "model_dump(by_alias=True)")
    print()

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 5 — Input passed to analyze_transaction_graph()
    # ─────────────────────────────────────────────────────────────────────────
    print("STAGE 5 -- Input list passed to analyze_transaction_graph()")
    # /analyze uses by_alias=False
    transfers_for_analytics = transfers_no_alias
    stage5_count = len(transfers_for_analytics)
    print(f"  COUNT = {stage5_count}")
    if stage5_count > 0:
        s = transfers_for_analytics[0]
        print(f"  Keys present: {list(s.keys())}")
        print(f"  'from_address' in keys: {'from_address' in s}")
        print(f"  'from' in keys:         {'from' in s}")
        print(f"  'to_address' in keys:   {'to_address' in s}")
        print(f"  'to' in keys:           {'to' in s}")
    print()

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 6 — graph_engine.build_transaction_graph()
    # ─────────────────────────────────────────────────────────────────────────
    print("STAGE 6 -- BlockchainGraphBuilder.build_transaction_graph()")
    builder = BlockchainGraphBuilder()

    # Simulate EXACTLY what the engine does internally and count skip-throughs
    skip_count = 0
    included_count = 0
    for tx in transfers_for_analytics:
        from_addr = str(tx.get("from_address", "")).lower()
        to_addr   = str(tx.get("to_address",   "")).lower()
        if not from_addr or not to_addr:
            skip_count += 1
        else:
            included_count += 1

    print(f"  Simulated filter using 'from_address'/'to_address' keys:")
    print(f"    Included (both non-empty): {included_count}")
    print(f"    SKIPPED  (one or both empty/missing): {skip_count}")

    # Also try with 'from'/'to' to show difference
    skip_alias = 0
    included_alias = 0
    for tx in transfers_for_analytics:
        from_addr = str(tx.get("from", "")).lower()
        to_addr   = str(tx.get("to",   "")).lower()
        if not from_addr or not to_addr:
            skip_alias += 1
        else:
            included_alias += 1

    print(f"\n  Simulated filter using 'from'/'to' alias keys:")
    print(f"    Included: {included_alias}")
    print(f"    Skipped:  {skip_alias}")

    # Now actually build and report
    graph = builder.build_transaction_graph(transfers_for_analytics, root_wallet=TARGET_WALLET)
    stage6_edges = graph.number_of_edges()
    stage6_nodes = graph.number_of_nodes()
    print(f"\n  Actual graph.number_of_edges() = {stage6_edges}  <-- transactions_analyzed")
    print(f"  Actual graph.number_of_nodes() = {stage6_nodes}  <-- wallets_discovered")

    # ─────────────────────────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────────────────────────
    print(SEPARATOR)
    print("  DIAGNOSTIC SUMMARY")
    print(SEPARATOR)
    print(f"  Stage 1  Alchemy transfers (direct):                {stage1_count}")
    print(f"  Stage 2  trace_result.summary.transfers_analyzed:   {stage2_count}")
    print(f"  Stage 3  trace_result.paths (raw objects):          {stage3_count}")
    print(f"  Stage 4  after model_dump(by_alias=False):          {stage4_count}")
    print(f"  Stage 5  input to analyze_transaction_graph():      {stage5_count}")
    print(f"  Stage 6  graph.number_of_edges():                   {stage6_edges}")
    print()

    if stage5_count > 0 and stage6_edges == 0:
        print("  >>> FAILURE POINT: Stage 5 -> Stage 6")
        print("  graph_engine looks up tx.get('from_address') and tx.get('to_address')")
        sample_keys = list(transfers_no_alias[0].keys()) if transfers_no_alias else []
        if "from" in sample_keys and "from_address" not in sample_keys:
            print("  BUT the dict contains 'from'/'to' (alias keys), NOT 'from_address'/'to_address'.")
            print("  CAUSE: model_dump(by_alias=False) still serializes with aliases because")
            print("         TracePathItem.model_config has serialize_by_alias=True,")
            print("         which overrides by_alias=False at the field level.")
        elif "from_address" in sample_keys:
            print("  'from_address' IS present -- check graph_engine skip logic more carefully.")
    elif stage3_count > 0 and stage4_count == 0:
        print("  >>> FAILURE POINT: Stage 3 -> Stage 4 (model_dump returned empty)")
    elif stage2_count == 0:
        print("  >>> FAILURE POINT: Stage 1 -> Stage 2 (tracer returned 0 paths)")
    elif stage1_count == 0:
        print("  >>> FAILURE POINT: Stage 1 -- Alchemy returned 0 transfers")
    else:
        print("  No obvious count drop detected in this run.")

    print(SEPARATOR)


if __name__ == "__main__":
    asyncio.run(run_diagnostic())
