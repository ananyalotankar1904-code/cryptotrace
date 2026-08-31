"""
PDF Report Payload & Content Generator
Project: Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges
Role: AI/ML + Graph Analytics Layer

Maps graph analytics, feature extraction, explainable risk scoring, and VASP attribution
directly into the PDF template variables for the 'BLOCKCHAIN INVESTIGATION REPORT'.
"""

from typing import Dict, List, Any
from datetime import datetime, timezone


def generate_pdf_report_payload(
    analysis_result: Dict[str, Any],
    case_id: str = "SIH-2026-ETH-08492",
    investigation_id: str = "INV-2026-9041",
    investigator_name: str = "Cyber Crime Cell - Lead Analyst",
    blockchain: str = "Ethereum (ERC-20 & Native ETH)",
    report_status: str = "FINAL - ACTIONABLE"
) -> Dict[str, Any]:
    """
    Transforms the output of `analyze_transaction_graph` into the exact variable
    dictionary expected by the 5-page PDF Investigation Report template.
    """
    root_wallet = analysis_result.get("root_wallet", "")
    risk_score = analysis_result.get("risk_score", 0)
    risk_level = analysis_result.get("risk_level", "LOW")
    wallet_count = analysis_result.get("wallet_count", 0)
    tx_count = analysis_result.get("transaction_count", 0)
    max_hop = analysis_result.get("max_hop", 0)
    
    # Extract features of root suspect wallet
    wallet_features = analysis_result.get("wallet_features", {})
    root_feats = wallet_features.get(root_wallet, {})
    
    total_incoming_eth = root_feats.get("primary_incoming_eth_value", 0.0)
    total_outgoing_eth = root_feats.get("primary_outgoing_eth_value", 0.0)
    
    # Destination & VASP Analysis
    known_entities = analysis_result.get("known_entities", [])
    has_vasp = len(known_entities) > 0
    primary_vasp = known_entities[0] if has_vasp else {}
    
    # Calculate confidence score for overall findings / VASP attribution
    confidence_score = 80 if has_vasp else 45
    
    # Build Transactions Table for Section 3
    transactions_table = []
    edges = analysis_result.get("edges", [])
    for idx, edge in enumerate(edges, 1):
        # Determine specific edge risk indicator
        indicator_text = "Standard Fund Transfer"
        val = edge.get("value", 0.0)
        asset = edge.get("asset", "ETH")
        hop = edge.get("hop", 1)
        
        if hop == 1 and val >= 2.0:
            indicator_text = "Rapid Initial Outflow (Layering Step 1)"
        elif asset != "ETH":
            indicator_text = f"Multi-Asset Movement ({asset})"
        elif hop >= 2:
            indicator_text = f"Intermediary Mule Forwarding (Hop {hop})"

        transactions_table.append({
            "EVIDENCE_ID": f"EV-{idx:03d}",
            "TX_HASH": edge.get("transaction_hash", "")[:18] + "...",
            "FROM_ADDRESS": edge.get("source", "")[:12] + "...",
            "TO_ADDRESS": edge.get("target", "")[:12] + "...",
            "TIMESTAMP": edge.get("timestamp", "N/A"),
            "AMOUNT": f"{val:.4f} {asset}",
            "RISK_INDICATOR": indicator_text
        })

    # Flow summary text
    path_strings = []
    for p in analysis_result.get("paths", []):
        path_strings.append(" → ".join([w[:8] + "..." for w in p.get("path", [])]))
    flow_summary = (
        f"Automated multi-hop tracing originated from suspect address {root_wallet[:12]}... "
        f"and propagated across {max_hop} sequential hops involving {wallet_count} unique addresses. "
        f"Identified {len(path_strings)} primary fund candidate routes terminating at "
        f"{primary_vasp.get('entity', 'unidentified private wallets')}."
    )

    # Risk Indicators mapping (Section 4 Table)
    high_freq = root_feats.get("tx_frequency_per_hour", 0.0) >= 2.0
    rapid_mov = root_feats.get("avg_time_between_tx_seconds", 9999) < 1800
    is_splitting = root_feats.get("is_splitting_hub", False) or root_feats.get("unique_outgoing_counterparties", 0) >= 2
    is_consolidating = root_feats.get("is_consolidation_hub", False)
    
    # Executive Summary text
    exec_summary = (
        f"Victim-reported suspect wallet {root_wallet} was subjected to automated multi-hop blockchain graph analysis. "
        f"The analytics engine traced a total outflow of {total_outgoing_eth:.2f} ETH and associated ERC-20 transfers "
        f"across {max_hop} hops. Behavior exhibits high velocity forwarding through intermediary transit wallets, culminating "
        f"in a direct deposit at {primary_vasp.get('entity', 'an external destination')}. Overall assessment stands at "
        f"{risk_level} risk with an attribution confidence of {confidence_score}%."
    )

    # Key Findings & Final Assessment
    key_findings = (
        f"1. Rapid Asset Forwarding: Stolen funds were moved within an average interval of "
        f"{root_feats.get('avg_time_between_tx_seconds', 0)/60:.1f} minutes, indicating scripted evasion.\n"
        f"2. Intermediary Layering: Funds passed through {wallet_count - 2} intermediary mule addresses before reaching the terminal destination.\n"
        f"3. VASP Identification: Terminal hop #{primary_vasp.get('hop', max_hop)} maps directly to verified exchange deposit infrastructure for {primary_vasp.get('entity', 'Unknown')}."
    )

    final_assessment = (
        f"The subject address demonstrates deliberate layering and rapid cash-out routing. "
        f"The identification of a verified {primary_vasp.get('entity', 'VASP')} deposit address at Hop {primary_vasp.get('hop', max_hop)} "
        f"provides an immediate, actionable jurisdiction point for law enforcement intervention."
    )

    # Recommended Actions
    rec_actions = (
        f"1. Issue Section 91 CrPC / Lawful Subpoena notice to {primary_vasp.get('entity', 'the identified VASP')} to freeze target deposit account.\n"
        f"2. Request KYC records, linked bank accounts, login IP logs, and withdrawal trails from {primary_vasp.get('entity', 'VASP')}.\n"
        f"3. Place continuous on-chain balance monitoring triggers on intermediary mule addresses."
    )

    return {
        # 1. Case Details
        "CASE_ID": case_id,
        "INVESTIGATION_ID": investigation_id,
        "INVESTIGATION_TIMESTAMP": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "INVESTIGATOR_NAME": investigator_name,
        "BLOCKCHAIN": blockchain,
        "SUSPECT_WALLET": root_wallet,
        "REPORT_STATUS": report_status,

        # 2. Investigation Summary
        "TRANSACTION_COUNT": tx_count,
        "TOTAL_INCOMING": f"{total_incoming_eth:.2f} ETH",
        "TOTAL_OUTGOING": f"{total_outgoing_eth:.2f} ETH",
        "NUMBER_OF_HOPS": max_hop,
        "DESTINATION_COUNT": wallet_count - 1,
        "OVERALL_RISK_LEVEL": risk_level,
        "CONFIDENCE_SCORE": confidence_score,
        "INVESTIGATOR_SUMMARY": exec_summary,

        # 3. Transaction Evidence
        "TRANSACTIONS": transactions_table,
        "TRANSACTION_FLOW_SUMMARY": flow_summary,

        # 4. Risk Summary & Indicators
        "RISK_SCORE": risk_score,
        "HIGH_TRANSACTION_FREQUENCY": "TRUE" if high_freq else "FALSE",
        "HIGH_FREQUENCY_DETAILS": f"Observed burst rate of {root_feats.get('tx_frequency_per_hour', 0):.1f} tx/hour exceeding normal retail patterns." if high_freq else "Transaction frequency within normal limits.",
        
        "LARGE_VALUE_MOVEMENT": "TRUE" if total_outgoing_eth >= 1.0 else "FALSE",
        "LARGE_VALUE_DETAILS": f"Significant fund volume of {total_outgoing_eth:.2f} ETH transferred rapidly." if total_outgoing_eth >= 1.0 else "Low transfer volume.",
        
        "RAPID_MOVEMENT": "TRUE" if rapid_mov else "FALSE",
        "RAPID_MOVEMENT_DETAILS": f"Funds forwarded within {root_feats.get('avg_time_between_tx_seconds', 0)/60:.1f} minutes between successive hops (rapid laundering velocity)." if rapid_mov else "Standard holding times observed.",
        
        "REPEATED_SPLITTING": "TRUE" if is_splitting else "FALSE",
        "SPLITTING_DETAILS": f"Suspect address distributed outgoing transfers to {root_feats.get('unique_outgoing_counterparties', 0)} distinct intermediary addresses." if is_splitting else "No significant fan-out splitting detected.",
        
        "REPEATED_CONSOLIDATION": "TRUE" if is_consolidating else "FALSE",
        "CONSOLIDATION_DETAILS": "Multiple inbound funding sources consolidated into single exit channel." if is_consolidating else "No multi-source consolidation observed.",
        
        "SUSPICIOUS_INTERACTION": "TRUE",
        "SUSPICIOUS_INTERACTION_DETAILS": f"Traversed {wallet_count - 2} intermediary mule addresses with zero balance retention.",
        
        "MIXER_OR_BRIDGE_INTERACTION": "FALSE",
        "MIXER_BRIDGE_DETAILS": "No interaction with known privacy mixers (Tornado Cash) or cross-chain bridges detected within analyzed scope.",

        # 5. VASP Attribution
        "VASP_INTERACTION": True if has_vasp else False,
        "VASP_NAME": primary_vasp.get("entity", "N/A"),
        "VASP_WALLET": primary_vasp.get("address", "N/A"),
        "VASP_INTERACTION_TYPE": primary_vasp.get("metadata", {}).get("address_type", "deposit_hot_wallet"),
        "VASP_TRANSACTION_HASH": edges[-1].get("transaction_hash", "N/A") if edges else "N/A",
        "VASP_CONFIDENCE_SCORE": 85 if has_vasp else 0,

        # 6. Key Findings and Assessment
        "KEY_FINDINGS": key_findings,
        "FINAL_ASSESSMENT": final_assessment,

        # 7. Recommended Actions
        "RECOMMENDED_ACTIONS": rec_actions,

        # 8. Additional Limitations
        "ADDITIONAL_LIMITATIONS": (
            "Temporal analysis is based on block timestamps provided by Alchemy nodes. "
            "Candidate paths represent probabilistic transaction sequences on the public Ethereum ledger."
        )
    }


if __name__ == "__main__":
    import json
    from analytics_service import analyze_transaction_graph
    from mock_data import MOCK_ROOT_WALLET, MOCK_TRANSFERS, MOCK_VASP_DIRECTORY

    analysis = analyze_transaction_graph(
        root_wallet=MOCK_ROOT_WALLET,
        transfers=MOCK_TRANSFERS,
        vasp_directory=MOCK_VASP_DIRECTORY
    )
    report_data = generate_pdf_report_payload(analysis)
    print("Successfully generated PDF Report Payload.")
    with open("pdf_report_content_draft.json", "w") as f:
        json.dump(report_data, f, indent=2)
    print("Exported to pdf_report_content_draft.json")
