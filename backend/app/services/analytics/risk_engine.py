"""
Explainable Rule-Based Risk Scoring Module
Project: Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges
Role: AI/ML + Graph Analytics Layer

IMPORTANT SEPARATION:
- Risk Score: Evaluates how suspicious/investigation-worthy transaction behavior is.
- VASP Attribution: Identifies which known exchange or entity an address belongs to.
Interaction with a known VASP does NOT automatically imply criminal guilt; it indicates
a potential cash-out exit point for KYC subpoena.
"""

from typing import Dict, List, Any, Optional


class ExplainableRiskScorer:
    """
    Computes deterministic, fully explainable risk scores (0-100) based on
    heuristic blockchain laundering patterns and graph topological indicators.
    """

    def __init__(self, thresholds: Optional[Dict[str, Any]] = None):
        # Configurable scoring weights and thresholds
        self.thresholds = thresholds or {
            "tier_low_max": 30,
            "tier_med_max": 60,
            "tier_high_max": 80,
            
            # Rule weights (additive point contributions)
            "base_suspect_score": 20,
            "rapid_transfers_weight": 20,
            "high_frequency_weight": 15,
            "multi_hop_intermediary_weight": 20,
            "splitting_weight": 15,
            "consolidation_weight": 15,
            "many_counterparties_weight": 10,
            "repeated_interactions_weight": 10
        }

    def compute_risk_score(
        self,
        root_wallet: str,
        graph_summary: Dict[str, Any],
        wallet_features: Dict[str, Any],
        all_features: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculates an explainable risk score for the investigation root/suspect wallet
        based on its local features and overall graph propagation patterns.
        """
        score = 0
        indicators = []
        details = []

        # 1. Base Prior for Victim-Reported Root Wallet
        base_pts = self.thresholds["base_suspect_score"]
        score += base_pts
        indicators.append("Victim-reported seed suspect wallet baseline")
        details.append({
            "code": "REPORTED_SUSPECT_PRIOR",
            "points": base_pts,
            "reason": f"Wallet {root_wallet[:10]}... was flagged as initial suspect address in victim incident report."
        })

        # 2. Multi-Hop Intermediary Depth
        max_hop = graph_summary.get("max_hop", 0)
        unique_wallets = graph_summary.get("unique_wallets", 0)
        if max_hop >= 3:
            pts = self.thresholds["multi_hop_intermediary_weight"]
            score += pts
            indicators.append(f"Deep multi-hop fund flow ({max_hop} hops across {unique_wallets} wallets)")
            details.append({
                "code": "DEEP_MULTI_HOP",
                "points": pts,
                "reason": f"Funds propagated across {max_hop} sequential hops, characteristic of layering behavior."
            })
        elif max_hop >= 2:
            pts = int(self.thresholds["multi_hop_intermediary_weight"] * 0.6)
            score += pts
            indicators.append(f"Multi-hop fund forwarding ({max_hop} hops detected)")
            details.append({
                "code": "MODERATE_MULTI_HOP",
                "points": pts,
                "reason": f"Funds routed through {max_hop} hops before terminal destination."
            })

        # 3. Rapid Successive Transfers / Short Intervals
        avg_interval = wallet_features.get("avg_time_between_tx_seconds", 0)
        time_span = wallet_features.get("time_span_seconds", 0)
        total_tx = wallet_features.get("total_tx_count", 0)

        if total_tx >= 2 and 0 < avg_interval <= 1800: # < 30 minutes average interval
            pts = self.thresholds["rapid_transfers_weight"]
            score += pts
            indicators.append("Rapid successive transfers (avg interval under 30 minutes)")
            details.append({
                "code": "RAPID_SUCCESSIVE_TRANSFERS",
                "points": pts,
                "reason": f"Transactions occurred in rapid succession with average interval of {round(avg_interval/60, 1)} minutes."
            })
        elif total_tx >= 2 and 1800 < avg_interval <= 7200: # < 2 hours
            pts = int(self.thresholds["rapid_transfers_weight"] * 0.5)
            score += pts
            indicators.append("Accelerated transaction turnover (under 2 hours)")
            details.append({
                "code": "ACCELERATED_TURNOVER",
                "points": pts,
                "reason": f"Turnover time averaged {round(avg_interval/3600, 1)} hours between transfers."
            })

        # 4. High Transaction Frequency
        freq = wallet_features.get("tx_frequency_per_hour", 0.0)
        if freq >= 2.0 and total_tx >= 3:
            pts = self.thresholds["high_frequency_weight"]
            score += pts
            indicators.append(f"High transaction frequency ({freq} tx/hour)")
            details.append({
                "code": "HIGH_TX_FREQUENCY",
                "points": pts,
                "reason": f"High burst rate of {freq} transactions per hour observed on suspect wallet."
            })

        # 5. Fund Splitting (Fan-Out) or Consolidation (Fan-In)
        is_splitting = wallet_features.get("is_splitting_hub", False)
        is_consolidating = wallet_features.get("is_consolidation_hub", False)

        if is_splitting:
            pts = self.thresholds["splitting_weight"]
            score += pts
            indicators.append("Fund splitting pattern detected (fan-out to multiple destinations)")
            details.append({
                "code": "FUND_SPLITTING",
                "points": pts,
                "reason": "Single wallet distributed funds outward to 3 or more distinct counterparty wallets."
            })

        if is_consolidating:
            pts = self.thresholds["consolidation_weight"]
            score += pts
            indicators.append("Fund consolidation pattern detected (fan-in from multiple sources)")
            details.append({
                "code": "FUND_CONSOLIDATION",
                "points": pts,
                "reason": "Wallet aggregated funds from 3 or more independent inbound senders."
            })

        # 6. Intermediary / Pass-Through Role Across Subgraph
        if all_features:
            intermediary_count = sum(1 for feat in all_features.values() if feat.get("is_intermediary"))
            if intermediary_count >= 2:
                pts = 10
                score += pts
                indicators.append(f"Network contains {intermediary_count} transit intermediary wallets")
                details.append({
                    "code": "TRANSIT_INTERMEDIARY_WALLETS",
                    "points": pts,
                    "reason": f"Found {intermediary_count} wallets in the path that both received and immediately forwarded funds."
                })

        # 7. Counterparty Spread & Repeated Interactions
        unique_cp = wallet_features.get("connected_wallets_count", 0)
        repeated_cp = wallet_features.get("repeated_interactions_count", 0)
        if unique_cp >= 4:
            pts = self.thresholds["many_counterparties_weight"]
            score += pts
            indicators.append(f"High counterparty spread ({unique_cp} connected wallets)")
            details.append({
                "code": "HIGH_COUNTERPARTY_SPREAD",
                "points": pts,
                "reason": f"Interacted with {unique_cp} distinct addresses during observed window."
            })

        if repeated_cp >= 2:
            pts = self.thresholds["repeated_interactions_weight"]
            score += pts
            indicators.append(f"Repeated transactions between fixed counterparties ({repeated_cp} addresses)")
            details.append({
                "code": "REPEATED_INTERACTIONS",
                "points": pts,
                "reason": f"Exhibited repeat transactions with {repeated_cp} specific counterparties."
            })

        # Clamp Score between 0 and 100
        final_score = min(100, max(0, score))

        # Determine Tier
        if final_score <= self.thresholds["tier_low_max"]:
            level = "LOW"
        elif final_score <= self.thresholds["tier_med_max"]:
            level = "MEDIUM"
        elif final_score <= self.thresholds["tier_high_max"]:
            level = "HIGH"
        else:
            level = "CRITICAL"

        return {
            "risk_score": final_score,
            "risk_level": level,
            "indicators": indicators,
            "indicator_details": details
        }
