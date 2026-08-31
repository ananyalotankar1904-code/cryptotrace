# Blockchain Graph Analytics & Explainable Risk Layer

**Project:** Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges from Victim-Reported Suspect Wallet Addresses through Automated Blockchain Analytics  
**Role:** AI/ML + Graph Analytics Engine  
**Target Environment:** Python 3.10+, NetworkX, FastAPI  

---

## 1. Overview & Pipeline Role

This module implements the **AI/ML + Graph Analytics Layer** for our Smart India Hackathon (SIH) prototype. It bridges the raw on-chain data collected from Alchemy/Ethereum with the investigator frontend dashboard:

```
[ Victim Incident Report ]
          ↓
[ Suspect Ethereum Address ]
          ↓
[ Member 3/4: Alchemy Web3 & Multi-Hop Tracing ]
          ↓
[ Normalized Transfer JSON (ETH + ERC-20) ]
          ↓
[ OUR LAYER: Graph Engine + Feature Extractor + Explainable Risk Scorer ]
          ↓
[ Member 2: VASP Attribution Match ] ──→ [ Member 6: Investigator Dashboard ]
```

---

## 2. Core Modules Summary

| File | Purpose / Deliverable | Key Interfaces |
| :--- | :--- | :--- |
| [`graph_engine.py`](file:///c:/SIH%2026/graph_engine.py) | **Directed Multi-Graph Builder** using NetworkX. Preserves multi-transfers between same addresses, avoids node duplication, computes hop distances, prevents cycles, and formats frontend JSON. | `BlockchainGraphBuilder`, `build_transaction_graph()`, `find_candidate_paths()`, `export_frontend_graph_json()` |
| [`feature_extractor.py`](file:///c:/SIH%2026/feature_extractor.py) | **Feature Extraction Module**. Calculates in/out degree, unique counterparties, multi-asset volumes, velocity/holding times, and intermediary transit flags. | `WalletFeatureExtractor`, `extract_wallet_features()`, `extract_all_wallets_features()` |
| [`risk_engine.py`](file:///c:/SIH%2026/risk_engine.py) | **Explainable Rule-Based Scorer**. Computes 0–100 risk score and generates human-readable audit reasons explaining **WHY** a score was assigned. | `ExplainableRiskScorer`, `compute_risk_score()` |
| [`analytics_service.py`](file:///c:/SIH%2026/analytics_service.py) | **Unified Service Controller (`POST /analyze`)**. Single entry point that orchestrates graph construction, feature extraction, scoring, VASP matching, and dashboard payload output. | `analyze_transaction_graph()`, `BlockchainAnalyticsService` |
| [`mock_data.py`](file:///c:/SIH%2026/mock_data.py) | **Synthetic Test Dataset**. Multi-hop flow (`A → B, A → C, B → D, B → E, D → F`) featuring ETH, USDT (ERC-20), repeated transfers, timestamps, and mock VASP deposit address. | `MOCK_ROOT_WALLET`, `MOCK_TRANSFERS`, `MOCK_VASP_DIRECTORY` |
| [`test_analytics.py`](file:///c:/SIH%2026/test_analytics.py) | **Comprehensive Unit Tests**. Tests all 9 required test scenarios (single hop, multi-hop, multi-edge, cycles, splitting, ERC-20, empty input, VASP match, risk scoring). | `python -m unittest test_analytics.py` |
| [`ml_roadmap.md`](file:///c:/SIH%2026/ml_roadmap.md) | **ML Research Note**. Explains MVP rules, ground-truth data requirements, and phased roadmap to Unsupervised Anomaly Detection and Graph Neural Networks. | Research & Architecture Documentation |

---

## 3. Team Interface Contracts

### A. Input from Member 4 (Data Ingestion / Multi-Hop Tracing)
Transfers passed to `analyze_transaction_graph()` must match the normalized format:
```json
[
  {
    "transaction_hash": "0xabc...",
    "from_address": "0x111...",
    "to_address": "0x222...",
    "asset": "ETH",
    "value": 1.5,
    "block_number": "19000000",
    "timestamp": "2026-08-30T10:00:00Z",
    "category": "external",
    "contract_address": null,
    "hop": 1
  },
  {
    "transaction_hash": "0xdef...",
    "from_address": "0x111...",
    "to_address": "0x222...",
    "asset": "USDT",
    "value": 2500.0,
    "block_number": "19000001",
    "timestamp": "2026-08-30T10:05:00Z",
    "category": "erc20",
    "contract_address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "hop": 1
  }
]
```

### B. Integration with Member 2 (VASP Intelligence Directory)
Known exchange and entity records are ingested as a dictionary lookup:
```json
{
  "0xbinancedepositaddress...": {
    "entity": "Binance",
    "entity_type": "KNOWN_VASP",
    "blockchain": "ethereum",
    "address_type": "deposit_hot_wallet",
    "confidence": "VERIFIED_OFFICIAL",
    "source": "FIU Registry"
  }
}
```

### C. Output to Member 6 (Investigator Dashboard)
The unified endpoint returns a complete payload containing nodes, edges, candidate paths, risk scores, and evidence explanations:
```json
{
  "root_wallet": "0xsuspect...",
  "wallet_count": 6,
  "transaction_count": 6,
  "max_hop": 3,
  "risk_score": 85,
  "risk_level": "CRITICAL",
  "risk_indicators": [
    "Victim-reported seed suspect wallet baseline",
    "Deep multi-hop fund flow (3 hops across 6 wallets)",
    "Rapid successive transfers (avg interval under 30 minutes)",
    "Network contains 2 transit intermediary wallets"
  ],
  "known_entities": [
    {
      "address": "0xbinancedeposit...",
      "entity": "Binance",
      "entity_type": "KNOWN_VASP",
      "hop": 3
    }
  ],
  "nodes": [
    { "id": "0xsuspect...", "type": "suspect", "hop": 0, "known_entity": null, "entity_type": null },
    { "id": "0xbinancedeposit...", "type": "wallet", "hop": 3, "known_entity": "Binance", "entity_type": "KNOWN_VASP" }
  ],
  "edges": [
    { "source": "0xsuspect...", "target": "0xmule...", "asset": "ETH", "value": 2.5, "transaction_hash": "0xtx1...", "hop": 1 }
  ],
  "paths": [
    { "path": ["0xsuspect...", "0xmule1...", "0xmule2...", "0xbinancedeposit..."], "hops": 3, "terminal_wallet": "0xbinancedeposit...", "terminal_entity": "Binance" }
  ]
}
```

---

## 4. Important Forensic & Investigation Limitation

> **LEGAL & FORENSIC NOTICE:**  
> A transaction path `A → B → C` indicates an observed **ledger relationship / fund-flow candidate path**. Because account-based blockchains (like Ethereum) pool balances inside account states, this prototype highlights *investigative priority*, not strict legal proof of fund commingling.  
> The system strictly separates:
> 1. **Risk Score**: *How suspicious / anomalous is the observed movement pattern?*
> 2. **VASP Attribution**: *Which verified exchange/service operates the destination address?*  
> Interaction with a known VASP does not imply criminal liability for the VASP; it marks the actionable legal entity for issuing KYC subpoena notices (e.g., Section 91 CrPC).

---

## 5. Running the Tests & Demo

```bash
# 1. Run full unit test suite (All 9 test cases)
python -m unittest test_analytics.py

# 2. Run standalone analysis service with mock dataset
python analytics_service.py

# 3. Run end-to-end multi-hop tracer and graph visualizer
python main_pipeline_demo.py
```
