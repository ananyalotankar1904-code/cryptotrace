"""
Comprehensive Unit Tests for Blockchain Analytics & Graph Engine
Project: Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges
Role: AI/ML + Graph Analytics Layer
"""

import unittest
from graph_engine import BlockchainGraphBuilder
from feature_extractor import WalletFeatureExtractor
from risk_engine import ExplainableRiskScorer
from analytics_service import analyze_transaction_graph


class TestBlockchainAnalytics(unittest.TestCase):

    def setUp(self):
        self.vasp_db = {
            "0xvasp_binance_deposit": {
                "entity": "Binance",
                "entity_type": "KNOWN_VASP",
                "confidence": "HIGH"
            }
        }
        self.builder = BlockchainGraphBuilder(self.vasp_db)
        self.risk_scorer = ExplainableRiskScorer()

    # -------------------------------------------------------------
    # TEST 1: Simple A -> B Graph
    # -------------------------------------------------------------
    def test_01_simple_a_to_b(self):
        transfers = [
            {
                "transaction_hash": "0xtx1",
                "from_address": "0xwallet_a",
                "to_address": "0xwallet_b",
                "asset": "ETH",
                "value": 1.0,
                "timestamp": "2026-08-30T10:00:00Z"
            }
        ]
        G = self.builder.build_transaction_graph(transfers, root_wallet="0xwallet_a")
        
        self.assertEqual(G.number_of_nodes(), 2)
        self.assertEqual(G.number_of_edges(), 1)
        self.assertEqual(G.nodes["0xwallet_a"]["hop"], 0)
        self.assertEqual(G.nodes["0xwallet_b"]["hop"], 1)

        paths = self.builder.find_candidate_paths("0xwallet_a")
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0]["path"], ["0xwallet_a", "0xwallet_b"])
        self.assertEqual(paths[0]["hops"], 1)

    # -------------------------------------------------------------
    # TEST 2: A -> B -> C Multi-Hop Graph
    # -------------------------------------------------------------
    def test_02_multi_hop_a_to_b_to_c(self):
        transfers = [
            {"transaction_hash": "0xtx1", "from_address": "0xa", "to_address": "0xb", "asset": "ETH", "value": 1.0, "hop": 1},
            {"transaction_hash": "0xtx2", "from_address": "0xb", "to_address": "0xc", "asset": "ETH", "value": 0.95, "hop": 2}
        ]
        G = self.builder.build_transaction_graph(transfers, root_wallet="0xa")
        summary = self.builder.get_root_analysis("0xa")

        self.assertEqual(summary["unique_wallets"], 3)
        self.assertEqual(summary["max_hop"], 2)
        self.assertEqual(G.nodes["0xc"]["hop"], 2)

        paths = self.builder.find_candidate_paths("0xa")
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0]["path"], ["0xa", "0xb", "0xc"])
        self.assertEqual(paths[0]["hops"], 2)

    # -------------------------------------------------------------
    # TEST 3: Repeated A -> B Transactions (Multi-Edges, No Node Duplication)
    # -------------------------------------------------------------
    def test_03_repeated_transactions_same_wallets(self):
        transfers = [
            {"transaction_hash": "0xtx1", "from_address": "0xa", "to_address": "0xb", "asset": "ETH", "value": 1.0},
            {"transaction_hash": "0xtx2", "from_address": "0xa", "to_address": "0xb", "asset": "ETH", "value": 0.5},
            {"transaction_hash": "0xtx3", "from_address": "0xa", "to_address": "0xb", "asset": "ETH", "value": 2.0}
        ]
        G = self.builder.build_transaction_graph(transfers, root_wallet="0xa")

        # Nodes MUST NOT be duplicated
        self.assertEqual(G.number_of_nodes(), 2)
        # All 3 transactions MUST be preserved as distinct edges
        self.assertEqual(G.number_of_edges(), 3)

        extractor = WalletFeatureExtractor(G)
        feats = extractor.extract_wallet_features("0xa")
        self.assertEqual(feats["outgoing_tx_count"], 3)
        self.assertEqual(feats["primary_outgoing_eth_value"], 3.5)
        self.assertEqual(feats["unique_outgoing_counterparties"], 1)

    # -------------------------------------------------------------
    # TEST 4: Cycle A -> B -> C -> A (No Infinite Loops)
    # -------------------------------------------------------------
    def test_04_cycle_prevention(self):
        transfers = [
            {"transaction_hash": "0xtx1", "from_address": "0xa", "to_address": "0xb", "asset": "ETH", "value": 1.0},
            {"transaction_hash": "0xtx2", "from_address": "0xb", "to_address": "0xc", "asset": "ETH", "value": 1.0},
            {"transaction_hash": "0xtx3", "from_address": "0xc", "to_address": "0xa", "asset": "ETH", "value": 1.0}
        ]
        G = self.builder.build_transaction_graph(transfers, root_wallet="0xa")

        # Path finding MUST NOT enter an infinite loop
        paths = self.builder.find_candidate_paths("0xa", max_depth=5)
        self.assertTrue(len(paths) > 0)
        # Verify no duplicate node in any individual path
        for p in paths:
            self.assertEqual(len(p["path"]), len(set(p["path"])))

    # -------------------------------------------------------------
    # TEST 5: Multiple Branches A -> B and A -> C (Splitting / Fan-Out)
    # -------------------------------------------------------------
    def test_05_multiple_branches_splitting(self):
        transfers = [
            {"transaction_hash": "0xtx1", "from_address": "0xa", "to_address": "0xb", "asset": "ETH", "value": 1.0},
            {"transaction_hash": "0xtx2", "from_address": "0xa", "to_address": "0xc", "asset": "ETH", "value": 2.0},
            {"transaction_hash": "0xtx3", "from_address": "0xa", "to_address": "0xd", "asset": "ETH", "value": 3.0}
        ]
        G = self.builder.build_transaction_graph(transfers, root_wallet="0xa")
        extractor = WalletFeatureExtractor(G)
        feats = extractor.extract_wallet_features("0xa")

        self.assertEqual(feats["unique_outgoing_counterparties"], 3)
        self.assertTrue(feats["is_splitting_hub"])

    # -------------------------------------------------------------
    # TEST 6: Multi-Asset (ETH + ERC-20 Transfers)
    # -------------------------------------------------------------
    def test_06_eth_and_erc20_multi_asset(self):
        transfers = [
            {
                "transaction_hash": "0xtx_eth",
                "from_address": "0xa",
                "to_address": "0xb",
                "asset": "ETH",
                "value": 1.5,
                "category": "external"
            },
            {
                "transaction_hash": "0xtx_usdt",
                "from_address": "0xa",
                "to_address": "0xb",
                "asset": "USDT",
                "value": 2500.0,
                "category": "erc20",
                "contract_address": "0xdAC17F958D2ee523a2206206994597C13D831ec7"
            }
        ]
        G = self.builder.build_transaction_graph(transfers, root_wallet="0xa")
        extractor = WalletFeatureExtractor(G)
        feats = extractor.extract_wallet_features("0xa")

        self.assertEqual(feats["unique_assets_count"], 2)
        self.assertIn("ETH", feats["assets_involved"])
        self.assertIn("USDT", feats["assets_involved"])
        self.assertEqual(feats["total_outgoing_value_by_asset"]["USDT"], 2500.0)

    # -------------------------------------------------------------
    # TEST 7: Empty Input
    # -------------------------------------------------------------
    def test_07_empty_input(self):
        result = analyze_transaction_graph(
            root_wallet="0xempty",
            transfers=[]
        )
        self.assertEqual(result["wallet_count"], 0)
        self.assertEqual(result["transaction_count"], 0)
        self.assertEqual(result["max_hop"], 0)
        self.assertEqual(len(result["nodes"]), 0)
        self.assertEqual(len(result["edges"]), 0)
        self.assertEqual(len(result["paths"]), 0)

    # -------------------------------------------------------------
    # TEST 8: Known VASP Address Matching (Separation of VASP from Risk)
    # -------------------------------------------------------------
    def test_08_known_vasp_match(self):
        transfers = [
            {
                "transaction_hash": "0xtx1",
                "from_address": "0xa",
                "to_address": "0xvasp_binance_deposit",
                "asset": "ETH",
                "value": 5.0
            }
        ]
        result = analyze_transaction_graph(
            root_wallet="0xa",
            transfers=transfers,
            vasp_directory=self.vasp_db
        )

        self.assertEqual(len(result["known_entities"]), 1)
        vasp_hit = result["known_entities"][0]
        self.assertEqual(vasp_hit["entity"], "Binance")
        self.assertEqual(vasp_hit["entity_type"], "KNOWN_VASP")
        self.assertEqual(vasp_hit["hop"], 1)

    # -------------------------------------------------------------
    # TEST 9: Explainable Risk Score Generation with Auditable Reasons
    # -------------------------------------------------------------
    def test_09_explainable_risk_scoring(self):
        from mock_data import MOCK_ROOT_WALLET, MOCK_TRANSFERS, MOCK_VASP_DIRECTORY
        result = analyze_transaction_graph(
            root_wallet=MOCK_ROOT_WALLET,
            transfers=MOCK_TRANSFERS,
            vasp_directory=MOCK_VASP_DIRECTORY
        )

        self.assertIn("risk_score", result)
        self.assertIn("risk_level", result)
        self.assertIn("risk_indicators", result)
        self.assertIn("risk_indicator_details", result)

        self.assertTrue(0 <= result["risk_score"] <= 100)
        self.assertIn(result["risk_level"], ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.assertTrue(len(result["risk_indicators"]) > 0)
        
        # Verify reason details have rule codes and points
        for detail in result["risk_indicator_details"]:
            self.assertIn("code", detail)
            self.assertIn("points", detail)
            self.assertIn("reason", detail)


if __name__ == "__main__":
    unittest.main()
