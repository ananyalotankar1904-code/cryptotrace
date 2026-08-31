"""
VASP Attribution Service
Project: SIH Crypto Fraud Intelligence Engine

Performs exact verified address matching against the VASP Intelligence Dataset.

Rules (from attribution_rules.json):
- R01: Exact verified match → confidence HIGH, status verified_dataset_match
- R04: No match → return UNKNOWN / no_verified_dataset_match

Matches only on the same blockchain (ethereum).
Normalizes addresses case-insensitively.
Prefers the nearest (lowest hop) verified downstream VASP.
"""

import json
import os
from typing import Dict, Any, List, Optional

# ── Dataset path ──────────────────────────────────────────────────────────────
_VASP_DATASET_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "vaspdataset", "vasp_intelligence_addresses.json"
)

# ── Cached dataset ─────────────────────────────────────────────────────────────
_VASP_RECORDS: Optional[List[Dict[str, Any]]] = None


def _load_vasp_records() -> List[Dict[str, Any]]:
    """Load and cache VASP records from the intelligence dataset."""
    global _VASP_RECORDS
    if _VASP_RECORDS is not None:
        return _VASP_RECORDS

    dataset_path = os.path.normpath(_VASP_DATASET_PATH)
    if not os.path.exists(dataset_path):
        # Fallback: search relative to cwd for the vaspdataset directory
        cwd_path = os.path.join(os.getcwd(), "vaspdataset", "vasp_intelligence_addresses.json")
        if os.path.exists(cwd_path):
            dataset_path = cwd_path
        else:
            _VASP_RECORDS = []
            return _VASP_RECORDS

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Only load records for ethereum and attribution_status == known_verified
    _VASP_RECORDS = [
        r for r in data.get("records", [])
        if r.get("blockchain", "").lower() == "ethereum"
        and r.get("attribution_status", "") == "known_verified"
    ]
    return _VASP_RECORDS


def _build_lookup() -> Dict[str, Dict[str, Any]]:
    """Build a lowercase address → record lookup dict from the dataset."""
    records = _load_vasp_records()
    return {r["address"].lower(): r for r in records}


def attribute_vasp_from_graph_nodes(
    graph_nodes: List[Dict[str, Any]],
    blockchain: str = "ethereum"
) -> Dict[str, Any]:
    """
    Perform exact verified address matching against all graph nodes.

    Iterates through graph nodes (which carry hop information) and checks each
    node's address against the verified VASP dataset. Returns the nearest (lowest
    hop) verified match, or a no-match sentinel.

    Args:
        graph_nodes: List of node dicts with keys: id, hop, known_entity, entity_type
        blockchain: Target blockchain to restrict matching (default: ethereum)

    Returns:
        VaspAttribution-compatible dict
    """
    lookup = _build_lookup()

    if not lookup:
        return _no_match()

    # Only match on the correct blockchain (already filtered at load time to ethereum)
    if blockchain.lower() != "ethereum":
        return _no_match()

    # Sort nodes by hop (ascending) so we prefer the nearest verified VASP
    sorted_nodes = sorted(
        [n for n in graph_nodes if n.get("id")],
        key=lambda n: (n.get("hop") if n.get("hop") is not None else 9999)
    )

    for node in sorted_nodes:
        addr_lower = node["id"].lower()
        record = lookup.get(addr_lower)
        if record:
            return _build_match(record, hop=node.get("hop"))

    return _no_match()


def attribute_vasp_from_transfers(
    transfers: List[Dict[str, Any]],
    blockchain: str = "ethereum"
) -> Dict[str, Any]:
    """
    Fallback: perform exact verified address matching against raw transfer records.
    Checks both from_address/to_address AND from/to field names (compatibility shim).

    Returns the match for the earliest-hop transfer that hits a verified VASP address.
    """
    lookup = _build_lookup()

    if not lookup:
        return _no_match()

    if blockchain.lower() != "ethereum":
        return _no_match()

    # Sort by hop (ascending) to prefer nearest match
    sorted_transfers = sorted(
        transfers,
        key=lambda t: (t.get("hop") if t.get("hop") is not None else 9999)
    )

    for tx in sorted_transfers:
        # Normalize field names (handle both from_address/to_address and from/to)
        to_addr = tx.get("to_address") or tx.get("to") or ""
        if to_addr:
            addr_lower = str(to_addr).lower()
            record = lookup.get(addr_lower)
            if record:
                return _build_match(record, hop=tx.get("hop"))

    return _no_match()


def _build_match(record: Dict[str, Any], hop: Optional[int]) -> Dict[str, Any]:
    """Construct a verified VASP attribution object from a dataset record."""
    return {
        "identified": True,
        "name": record.get("entity"),
        "type": record.get("entity_type"),
        "address_type": record.get("address_type"),
        "matched_address": record.get("address"),
        "match_type": "exact_verified_address",
        "confidence": record.get("confidence"),
        "confidence_score": record.get("confidence_score"),
        "hop": hop,
        "evidence": record.get("source_url"),
        "source_name": record.get("source_name"),
        "notes": record.get("notes"),
        "status": "verified_dataset_match",
    }


def _no_match() -> Dict[str, Any]:
    """Construct the no-match VASP attribution sentinel."""
    return {
        "identified": False,
        "name": None,
        "type": None,
        "address_type": None,
        "matched_address": None,
        "match_type": "none",
        "confidence": None,
        "confidence_score": None,
        "hop": None,
        "evidence": None,
        "source_name": None,
        "notes": None,
        "status": "no_verified_dataset_match",
    }
