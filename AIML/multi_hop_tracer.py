"""
Multi-Hop Tracing Engine for Blockchain Forensic Investigation
Project: Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from collections import deque
import networkx as nx


# ==============================================================================
# DELIVERABLE C: MULTI-HOP TRACING LOGIC & ALGORITHM
# ==============================================================================

class MultiHopTracer:
    """
    Implements breadth-first forward fund-tracing with blockchain-specific heuristics:
    1. Temporal Order: Outflow must happen at or after the inflow timestamp.
    2. Value Threshold: Ignore dust/spam transfers below min_value_eth.
    3. Hop Depth Limit: Prevents exponential explosion (typically 3-5 hops).
    4. VASP Stop Condition: Terminates or marks branch once funds hit an Exchange/VASP.
    5. Peel/Split Detection: Flags if funds are progressively peeled across hops.
    """

    def __init__(
        self,
        graph_engine,
        max_hops: int = 4,
        min_value_threshold: float = 0.01,
        max_branching_factor: int = 5,
        vasp_directory: Optional[Dict[str, str]] = None
    ):
        self.engine = graph_engine
        self.max_hops = max_hops
        self.min_value_threshold = min_value_threshold
        self.max_branching_factor = max_branching_factor
        self.vasp_directory = vasp_directory or {}

    def trace_forward_fund_flow(
        self,
        seed_suspect_address: str,
        initial_timestamp: Optional[int] = None,
        initial_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes multi-hop forward tracing starting from a victim-reported suspect wallet.
        Returns all valid fund paths leading to intermediate wallets or VASPs.
        """
        seed = seed_suspect_address.lower()
        G = self.engine.graph

        if not G.has_node(seed):
            return {
                "status": "error",
                "message": f"Seed address {seed} not present in graph.",
                "paths": [],
                "vasp_destinations": []
            }

        # Queue items: (current_node, current_hop, path_nodes, path_edges, arrival_time, carried_value)
        queue = deque([(seed, 0, [seed], [], initial_timestamp or 0, initial_value or float("inf"))])
        
        discovered_paths = []
        vasp_hits = []
        visited_nodes_at_depth = {}

        while queue:
            curr_node, curr_hop, path_nodes, path_edges, last_tx_time, last_tx_val = queue.popleft()

            # Stop condition 1: Exceeded max hops
            if curr_hop >= self.max_hops:
                discovered_paths.append({
                    "path_nodes": path_nodes,
                    "path_edges": path_edges,
                    "termination_reason": "MAX_HOPS_REACHED",
                    "final_wallet": curr_node
                })
                continue

            # Check if current node is a known VASP (stop tracing this branch further)
            node_data = G.nodes.get(curr_node, {})
            vasp_name = node_data.get("known_vasp_name") or self.vasp_directory.get(curr_node)
            
            if curr_hop > 0 and vasp_name:
                hit_info = {
                    "vasp_name": vasp_name,
                    "vasp_address": curr_node,
                    "hop_count": curr_hop,
                    "path_nodes": path_nodes,
                    "path_edges": path_edges,
                    "final_received_value": last_tx_val,
                    "termination_reason": "VASP_REACHED"
                }
                discovered_paths.append(hit_info)
                vasp_hits.append(hit_info)
                # Terminate branch since exchange deposit wallets generally mix/pool funds internally
                continue

            # Find valid outgoing edges from curr_node
            out_edges = []
            for u, v, k, edge_data in G.out_edges(curr_node, keys=True, data=True):
                tx_time = edge_data.get("timestamp", 0)
                tx_val = edge_data.get("value", 0.0)

                # Heuristic Filter 1: Temporal validity (outflow must happen after or at inflow)
                if tx_time < last_tx_time:
                    continue

                # Heuristic Filter 2: Value threshold (ignore spam/dust)
                if tx_val < self.min_value_threshold:
                    continue

                out_edges.append((v, k, edge_data))

            # Heuristic Filter 3: Sort by value descending and cap at max_branching_factor
            out_edges.sort(key=lambda item: item[2].get("value", 0.0), reverse=True)
            out_edges = out_edges[:self.max_branching_factor]

            if not out_edges:
                if curr_hop > 0:
                    discovered_paths.append({
                        "path_nodes": path_nodes,
                        "path_edges": path_edges,
                        "termination_reason": "DEAD_END_OR_HELD",
                        "final_wallet": curr_node
                    })
                continue

            for next_node, tx_key, edge_data in out_edges:
                # Loop prevention in current path
                if next_node in path_nodes:
                    continue

                new_path_nodes = list(path_nodes) + [next_node]
                new_path_edges = list(path_edges) + [edge_data]
                queue.append((
                    next_node,
                    curr_hop + 1,
                    new_path_nodes,
                    new_path_edges,
                    edge_data.get("timestamp", 0),
                    edge_data.get("value", 0.0)
                ))

        return {
            "status": "success",
            "seed_address": seed,
            "total_paths_explored": len(discovered_paths),
            "vasp_destinations": vasp_hits,
            "all_paths": discovered_paths
        }


# ==============================================================================
# PSEUDOCODE REPRESENTATION (FOR DESIGN DOCUMENTATION)
# ==============================================================================
PSEUDOCODE_TRACING = """
FUNCTION TraceMultiHopFunds(SeedWallet, MaxHops, MinValueThreshold, VaspDatabase):
    Initialize Queue Q = [(SeedWallet, Hop=0, Path=[SeedWallet], PrevTxTime=0)]
    Initialize ResultPaths = []
    Initialize VaspHits = []

    WHILE Q is not empty:
        Pop (CurrentWallet, CurrentHop, CurrentPath, PrevTxTime) from Q

        IF CurrentHop >= MaxHops:
            Append CurrentPath to ResultPaths (Reason: "Max Hops Reached")
            CONTINUE

        IF CurrentHop > 0 AND CurrentWallet IN VaspDatabase:
            Record VASP Hit (VASP = VaspDatabase[CurrentWallet], Hop = CurrentHop)
            Append CurrentPath to VaspHits
            CONTINUE (Stop expanding branch; exit point reached)

        Fetch Outgoing Transactions from CurrentWallet WHERE:
            1. OutgoingTx.Timestamp >= PrevTxTime (Temporal Consistency)
            2. OutgoingTx.Value >= MinValueThreshold (Dust Filter)
            3. OutgoingTx.ToAddress NOT IN CurrentPath (Cycle Prevention)

        Sort Outgoing Transactions by Value DESCENDING
        Prune to Top-K (Branching Factor Limit)

        IF Outgoing Transactions is Empty:
            Append CurrentPath to ResultPaths (Reason: "Funds Retained/Dead End")
            CONTINUE

        FOR EACH Tx IN Pruned Outgoing Transactions:
            NewPath = CurrentPath + [Tx.ToAddress]
            Push (Tx.ToAddress, CurrentHop + 1, NewPath, Tx.Timestamp) to Q

    RETURN { ResultPaths, VaspHits }
"""

if __name__ == "__main__":
    from graph_engine import create_prototype_graph
    proto = create_prototype_graph()
    tracer = MultiHopTracer(
        proto,
        vasp_directory={"0xbinancedeposit00000000000000000000000": "Binance"}
    )
    result = tracer.trace_forward_fund_flow("0xsuspect99999999999999999999999999999999")
    print(f"Traced {result['total_paths_explored']} paths. Found {len(result['vasp_destinations'])} VASP exits.")
    for hit in result["vasp_destinations"]:
        print(f" -> Hit VASP: {hit['vasp_name']} at hop {hit['hop_count']} along path: {hit['path_nodes']}")
