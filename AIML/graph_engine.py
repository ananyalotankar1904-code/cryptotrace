"""
Graph Building & Topological Analysis Module
Project: Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges
Role: AI/ML + Graph Analytics Layer
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
import networkx as nx


class BlockchainGraphBuilder:
    """
    Builds and manages the directed multi-graph of Ethereum and ERC-20 transfers.
    Preserves all transaction-level metadata while maintaining unique wallet nodes.
    """

    def __init__(self, vasp_directory: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        :param vasp_directory: Optional Member 2 known VASP intelligence directory.
               Format: { "0x...": { "entity": "Binance", "entity_type": "VASP", "confidence": "HIGH" } }
        """
        self.graph = nx.MultiDiGraph()
        self.vasp_directory = {k.lower(): v for k, v in (vasp_directory or {}).items()}

    def register_vasp_directory(self, vasp_directory: Dict[str, Dict[str, Any]]):
        """Updates the known VASP lookup table from Member 2's dataset."""
        for addr, meta in vasp_directory.items():
            self.vasp_directory[addr.lower()] = meta

    def build_transaction_graph(
        self,
        transfers: List[Dict[str, Any]],
        root_wallet: Optional[str] = None
    ) -> nx.MultiDiGraph:
        """
        Ingests normalized transfer records from Member 4 / Alchemy backend.
        Preserves individual transfers as multi-edges and adds rich node/edge attributes.
        """
        self.graph.clear()
        normalized_root = root_wallet.lower() if root_wallet else None

        for tx in transfers:
            from_addr = str(tx.get("from_address", "")).lower()
            to_addr = str(tx.get("to_address", "")).lower()

            if not from_addr or not to_addr:
                continue

            # Add nodes with initial metadata
            self._ensure_node(from_addr, normalized_root)
            self._ensure_node(to_addr, normalized_root)

            # Extract transfer attributes preserving ETH vs ERC-20
            tx_hash = tx.get("transaction_hash", "")
            asset = tx.get("asset", "ETH")
            value = float(tx.get("value", 0.0) or 0.0)
            block_number = str(tx.get("block_number", ""))
            timestamp = tx.get("timestamp")
            category = tx.get("category", "external")
            contract_address = tx.get("contract_address")
            hop = tx.get("hop")

            # Unique key for MultiDiGraph: tx_hash + asset + category (allows multiple transfers in same tx)
            edge_key = f"{tx_hash}_{asset}_{len(self.graph.get_edge_data(from_addr, to_addr) or {})}"

            self.graph.add_edge(
                from_addr,
                to_addr,
                key=edge_key,
                transaction_hash=tx_hash,
                asset=asset,
                value=value,
                block_number=block_number,
                timestamp=timestamp,
                category=category,
                contract_address=contract_address,
                hop=hop
            )

        # Calculate/Validate Hop distances from Root Wallet if provided
        if normalized_root and self.graph.has_node(normalized_root):
            self._compute_and_annotate_hops(normalized_root)

        return self.graph

    def _ensure_node(self, address: str, root_wallet: Optional[str] = None):
        """Ensures a wallet node exists with proper classification and known entity tags."""
        if not self.graph.has_node(address):
            node_type = "wallet"
            if root_wallet and address == root_wallet:
                node_type = "suspect"

            # Check Member 2 VASP intelligence dataset
            vasp_info = self.vasp_directory.get(address)
            known_entity = vasp_info.get("entity") if isinstance(vasp_info, dict) else None
            entity_type = vasp_info.get("entity_type", "KNOWN_VASP") if isinstance(vasp_info, dict) else None

            self.graph.add_node(
                address,
                id=address,
                type=node_type,
                hop=0 if (root_wallet and address == root_wallet) else None,
                known_entity=known_entity,
                entity_type=entity_type,
                vasp_metadata=vasp_info if isinstance(vasp_info, dict) else {}
            )

    def _compute_and_annotate_hops(self, root_wallet: str):
        """
        Computes the shortest path distance (hop depth) from root wallet
        using BFS, annotating each node in the graph.
        """
        lengths = nx.single_source_shortest_path_length(self.graph, root_wallet)
        for node, distance in lengths.items():
            self.graph.nodes[node]["hop"] = distance

    def get_root_analysis(self, root_wallet: str) -> Dict[str, Any]:
        """
        Returns high-level graph topology relative to the suspect wallet.
        """
        norm_root = root_wallet.lower()
        if not self.graph.has_node(norm_root):
            return {
                "root_wallet": norm_root,
                "unique_wallets": self.graph.number_of_nodes(),
                "max_hop": 0,
                "reachable_wallets": 0
            }

        lengths = nx.single_source_shortest_path_length(self.graph, norm_root)
        max_hop = max(lengths.values()) if lengths else 0

        return {
            "root_wallet": norm_root,
            "unique_wallets": self.graph.number_of_nodes(),
            "max_hop": max_hop,
            "reachable_wallets": len(lengths)
        }

    def find_candidate_paths(
        self,
        root_wallet: str,
        max_depth: int = 4,
        max_paths: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Discovers candidate fund-flow relationship paths starting from the root wallet.
        Uses depth-limited DFS with cycle prevention to avoid infinite loops.
        """
        norm_root = root_wallet.lower()
        if not self.graph.has_node(norm_root):
            return []

        all_paths = []

        def dfs(current_node: str, current_path: List[str]):
            if len(all_paths) >= max_paths:
                return

            # Check outbound neighbors
            out_neighbors = list(self.graph.successors(current_node))
            has_valid_next_step = False

            for nxt in out_neighbors:
                if nxt not in current_path:  # Cycle prevention
                    has_valid_next_step = True
                    if len(current_path) < max_depth + 1:
                        dfs(nxt, current_path + [nxt])

            # If leaf node or max depth reached and path has at least 1 hop
            if (not has_valid_next_step or len(current_path) == max_depth + 1) and len(current_path) > 1:
                # Check if this exact path is already recorded
                if current_path not in [p["path"] for p in all_paths]:
                    # Extract edge metadata along the path
                    path_edges_summary = []
                    for i in range(len(current_path) - 1):
                        u, v = current_path[i], current_path[i+1]
                        edges_dict = self.graph.get_edge_data(u, v) or {}
                        for k, d in edges_dict.items():
                            path_edges_summary.append({
                                "from": u,
                                "to": v,
                                "asset": d.get("asset"),
                                "value": d.get("value"),
                                "tx_hash": d.get("transaction_hash"),
                                "timestamp": d.get("timestamp")
                            })

                    all_paths.append({
                        "path": current_path,
                        "hops": len(current_path) - 1,
                        "terminal_wallet": current_path[-1],
                        "terminal_entity": self.graph.nodes[current_path[-1]].get("known_entity"),
                        "transfers": path_edges_summary
                    })

        dfs(norm_root, [norm_root])
        # Sort paths by hop length ascending
        all_paths.sort(key=lambda x: x["hops"])
        return all_paths[:max_paths]

    def export_frontend_graph_json(self) -> Dict[str, Any]:
        """
        Exports clean, normalized JSON graph payload specifically designed
        for Member 6's investigator frontend dashboard.
        """
        nodes_list = []
        for node_id, data in self.graph.nodes(data=True):
            node_payload = {
                "id": node_id,
                "type": data.get("type", "wallet"),
                "hop": data.get("hop", None),
                "known_entity": data.get("known_entity", None),
                "entity_type": data.get("entity_type", None)
            }
            nodes_list.append(node_payload)

        edges_list = []
        for u, v, key, data in self.graph.edges(keys=True, data=True):
            edge_payload = {
                "source": u,
                "target": v,
                "asset": data.get("asset", "ETH"),
                "value": data.get("value", 0.0),
                "transaction_hash": data.get("transaction_hash", ""),
                "timestamp": data.get("timestamp"),
                "block_number": data.get("block_number"),
                "category": data.get("category", "external"),
                "hop": data.get("hop")
            }
            edges_list.append(edge_payload)

        return {
            "nodes": nodes_list,
            "edges": edges_list
        }
