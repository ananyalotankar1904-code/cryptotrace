"""
Wallet & Graph Feature Extraction Module
Project: Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges
Role: AI/ML + Graph Analytics Layer

DISCLAIMER:
Features extracted in this module are purely topological and behavioral
INVESTIGATION INDICATORS. They do not constitute proof of criminal liability.
"""

from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
from datetime import datetime
import networkx as nx


class WalletFeatureExtractor:
    """
    Extracts topological, volume, multi-asset, and temporal indicators
    from a populated NetworkX MultiDiGraph for individual wallets and overall graph.
    """

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    def extract_wallet_features(self, address: str) -> Dict[str, Any]:
        """
        Extracts all investigative indicators for a specific wallet node.
        """
        addr = address.lower()
        if not self.graph.has_node(addr):
            return {}

        node_data = self.graph.nodes[addr]

        # 1. Edge Ingestion & Categorization
        in_edges = list(self.graph.in_edges(addr, data=True))
        out_edges = list(self.graph.out_edges(addr, data=True))

        in_tx_count = len(in_edges)
        out_tx_count = len(out_edges)
        total_tx_count = in_tx_count + out_tx_count

        # 2. Counterparty Analysis
        in_senders = [u for u, _, _ in in_edges]
        out_receivers = [v for _, v, _ in out_edges]

        unique_in_senders = set(in_senders)
        unique_out_receivers = set(out_receivers)
        all_connected_wallets = unique_in_senders.union(unique_out_receivers)

        # Counterparty Interaction Frequency (Repeated interactions)
        counterparty_counts = defaultdict(int)
        for s in in_senders:
            counterparty_counts[s] += 1
        for r in out_receivers:
            counterparty_counts[r] += 1

        repeated_interaction_count = sum(1 for cp, count in counterparty_counts.items() if count > 1)

        # 3. Value & Multi-Asset Analysis
        in_value_by_asset = defaultdict(float)
        out_value_by_asset = defaultdict(float)
        assets_observed = set()

        for _, _, data in in_edges:
            asset = data.get("asset", "ETH")
            val = float(data.get("value", 0.0) or 0.0)
            in_value_by_asset[asset] += val
            assets_observed.add(asset)

        for _, _, data in out_edges:
            asset = data.get("asset", "ETH")
            val = float(data.get("value", 0.0) or 0.0)
            out_value_by_asset[asset] += val
            assets_observed.add(asset)

        total_in_eth_equiv = in_value_by_asset.get("ETH", 0.0)
        total_out_eth_equiv = out_value_by_asset.get("ETH", 0.0)

        # 4. Temporal Dynamics & Frequency
        timestamps = []
        for _, _, data in in_edges + out_edges:
            ts_str = data.get("timestamp")
            if ts_str:
                ts_val = self._parse_timestamp(ts_str)
                if ts_val:
                    timestamps.append(ts_val)

        timestamps.sort()
        tx_frequency_per_hour = 0.0
        avg_time_between_tx_sec = 0.0
        time_span_seconds = 0.0

        if len(timestamps) >= 2:
            time_span_seconds = timestamps[-1] - timestamps[0]
            intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
            avg_time_between_tx_sec = sum(intervals) / len(intervals)
            span_hours = max(time_span_seconds / 3600.0, 0.001)
            tx_frequency_per_hour = round(len(timestamps) / span_hours, 2)

        # 5. Role and Structural Classification
        is_intermediary = (in_tx_count > 0 and out_tx_count > 0)
        is_consolidation_hub = (len(unique_in_senders) >= 3 and len(unique_out_receivers) <= 1)
        is_splitting_hub = (len(unique_out_receivers) >= 3 and len(unique_in_senders) <= 1)

        return {
            "address": addr,
            "hop_from_root": node_data.get("hop"),
            "node_type": node_data.get("type", "wallet"),
            "known_entity": node_data.get("known_entity"),
            "entity_type": node_data.get("entity_type"),
            
            # Transaction Counts
            "incoming_tx_count": in_tx_count,
            "outgoing_tx_count": out_tx_count,
            "total_tx_count": total_tx_count,

            # Counterparty Metrics
            "unique_incoming_counterparties": len(unique_in_senders),
            "unique_outgoing_counterparties": len(unique_out_receivers),
            "connected_wallets_count": len(all_connected_wallets),
            "repeated_interactions_count": repeated_interaction_count,

            # Asset & Value Metrics
            "unique_assets_count": len(assets_observed),
            "assets_involved": list(assets_observed),
            "total_incoming_value_by_asset": dict(in_value_by_asset),
            "total_outgoing_value_by_asset": dict(out_value_by_asset),
            "primary_incoming_eth_value": total_in_eth_equiv,
            "primary_outgoing_eth_value": total_out_eth_equiv,

            # Temporal Indicators
            "earliest_timestamp": timestamps[0] if timestamps else None,
            "latest_timestamp": timestamps[-1] if timestamps else None,
            "time_span_seconds": round(time_span_seconds, 1),
            "avg_time_between_tx_seconds": round(avg_time_between_tx_sec, 1),
            "tx_frequency_per_hour": tx_frequency_per_hour,

            # Structural Indicators
            "is_intermediary": is_intermediary,
            "is_consolidation_hub": is_consolidation_hub,
            "is_splitting_hub": is_splitting_hub
        }

    def extract_all_wallets_features(self) -> Dict[str, Dict[str, Any]]:
        """Extracts features for every wallet node in the graph."""
        return {
            node: self.extract_wallet_features(node)
            for node in self.graph.nodes()
        }

    def _parse_timestamp(self, ts_input: Any) -> Optional[float]:
        """Converts ISO 8601 strings or Unix epoch integers into float timestamps."""
        if isinstance(ts_input, (int, float)):
            return float(ts_input)
        if isinstance(ts_input, str):
            try:
                # Handle ISO formats e.g. 2026-08-30T10:00:00Z
                clean_ts = ts_input.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_ts)
                return dt.timestamp()
            except Exception:
                try:
                    return float(ts_input)
                except Exception:
                    return None
        return None
