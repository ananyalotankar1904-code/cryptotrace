"""
Unified Analytics Service / Endpoint Module
Project: Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges
Role: AI/ML + Graph Analytics Layer

Provides the primary analysis function for FastAPI backend (`POST /analyze`)
and orchestrates graph building, feature extraction, explainable scoring, and frontend formatting.
"""

from typing import Dict, List, Any, Optional
from .graph_engine import BlockchainGraphBuilder
from .feature_extractor import WalletFeatureExtractor
from .risk_engine import ExplainableRiskScorer


class BlockchainAnalyticsService:
    """
    Main controller for AI/ML + Graph Analytics Layer.
    Exposes unified `analyze_investigation` method matching the API contract for Member 4 & 6.
    """

    def __init__(self, vasp_directory: Optional[Dict[str, Dict[str, Any]]] = None):
        self.vasp_directory = vasp_directory or {}
        self.builder = BlockchainGraphBuilder(self.vasp_directory)
        self.risk_scorer = ExplainableRiskScorer()

    def update_vasp_intelligence(self, vasp_directory: Dict[str, Dict[str, Any]]):
        """Updates Member 2's known VASP directory."""
        self.vasp_directory.update(vasp_directory)
        self.builder.register_vasp_directory(self.vasp_directory)

    def analyze_investigation(
        self,
        root_wallet: str,
        transfers: List[Dict[str, Any]],
        vasp_directory: Optional[Dict[str, Dict[str, Any]]] = None,
        max_path_depth: int = 4,
        max_paths: int = 10
    ) -> Dict[str, Any]:
        """
        Executes end-to-end graph construction, feature extraction,
        explainable risk scoring, VASP entity matching, and frontend JSON formatting.
        """
        norm_root = root_wallet.lower()

        # Update VASP directory if provided in the call
        if vasp_directory:
            self.update_vasp_intelligence(vasp_directory)

        # 1. Build Graph
        graph = self.builder.build_transaction_graph(transfers, root_wallet=norm_root)

        # 2. Compute Topology & Hop Summary
        topo_summary = self.builder.get_root_analysis(norm_root)

        # 3. Extract Features for Wallets
        extractor = WalletFeatureExtractor(graph)
        all_wallet_features = extractor.extract_all_wallets_features()
        root_features = all_wallet_features.get(norm_root, {})

        # 4. Compute Explainable Risk Score
        risk_result = self.risk_scorer.compute_risk_score(
            root_wallet=norm_root,
            graph_summary=topo_summary,
            wallet_features=root_features,
            all_features=all_wallet_features
        )

        # 5. Extract Candidate Relationship Paths from Root
        candidate_paths = self.builder.find_candidate_paths(
            root_wallet=norm_root,
            max_depth=max_path_depth,
            max_paths=max_paths
        )

        # 6. Extract Known Entities Present in the Graph (VASP Attribution Layer)
        known_entities = []
        for node_id, data in graph.nodes(data=True):
            if data.get("known_entity"):
                known_entities.append({
                    "address": node_id,
                    "entity": data.get("known_entity"),
                    "entity_type": data.get("entity_type", "KNOWN_VASP"),
                    "hop": data.get("hop"),
                    "metadata": data.get("vasp_metadata", {})
                })

        # 7. Generate Frontend Graph JSON (Member 6 UI ready)
        frontend_graph = self.builder.export_frontend_graph_json()

        # 8. Assemble Full Response Payload
        return {
            "root_wallet": norm_root,
            "wallet_count": topo_summary["unique_wallets"],
            "transaction_count": graph.number_of_edges(),
            "max_hop": topo_summary["max_hop"],
            "risk_score": risk_result["risk_score"],
            "risk_level": risk_result["risk_level"],
            "risk_indicators": risk_result["indicators"],
            "risk_indicator_details": risk_result["indicator_details"],
            "known_entities": known_entities,
            "nodes": frontend_graph["nodes"],
            "edges": frontend_graph["edges"],
            "paths": candidate_paths,
            "wallet_features": all_wallet_features,
            "disclaimer": (
                "INVESTIGATION NOTICE: Analyzed paths represent transaction relationship "
                "candidate flows and risk indicators based on observable ledger transfers. "
                "They do not constitute conclusive forensic proof of specific fund commingling "
                "or legal criminal guilt."
            )
        }


# Convenience standalone function matching `POST /analyze`
def analyze_transaction_graph(
    root_wallet: str,
    transfers: List[Dict[str, Any]],
    vasp_directory: Optional[Dict[str, Dict[str, Any]]] = None,
    max_path_depth: int = 4,
    max_paths: int = 10
) -> Dict[str, Any]:
    """Helper wrapper for direct invocation in FastAPI / scripts."""
    service = BlockchainAnalyticsService(vasp_directory)
    return service.analyze_investigation(
        root_wallet=root_wallet,
        transfers=transfers,
        max_path_depth=max_path_depth,
        max_paths=max_paths
    )


if __name__ == "__main__":
    import json
    from mock_data import MOCK_ROOT_WALLET, MOCK_TRANSFERS, MOCK_VASP_DIRECTORY

    print("Running Blockchain Analytics Service on Synthetic Dataset...")
    result = analyze_transaction_graph(
        root_wallet=MOCK_ROOT_WALLET,
        transfers=MOCK_TRANSFERS,
        vasp_directory=MOCK_VASP_DIRECTORY
    )
    print(f"\nRoot Wallet: {result['root_wallet']}")
    print(f"Total Wallets: {result['wallet_count']} | Total Transactions: {result['transaction_count']} | Max Hop: {result['max_hop']}")
    print(f"Risk Score: {result['risk_score']} ({result['risk_level']})")
    print(f"Risk Indicators: {result['risk_indicators']}")
    print(f"Known Entities Identified: {len(result['known_entities'])}")
    for entity in result['known_entities']:
        print(f" -> {entity['entity']} ({entity['entity_type']}) at Hop {entity['hop']} [Addr: {entity['address'][:12]}...]")
    print(f"Discovered Candidate Paths: {len(result['paths'])}")
