# AI/ML Roadmap: MVP Rule-Based Analytics → Future ML Enhancement

**Project:** Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges from Victim-Reported Suspect Wallet Addresses through Automated Blockchain Analytics  
**Subsystem:** AI/ML + Graph Analytics Layer  

---

## 1. Executive Summary

In cryptocurrency forensic investigations, an AI model that acts as an unexplainable "black box" cannot be used in a court of law or for issuing freezing directives (e.g., Section 91 CrPC notices). 

For the **SIH Hackathon Prototype (MVP)**, we implement a **deterministic, rule-based graph analytics engine** that guarantees $100\%$ explainability, zero hallucination, and full auditability. 

This document outlines:
1. What our current MVP rules accomplish.
2. Why deep learning / GNNs cannot be reliably deployed without specialized ground-truth datasets.
3. A phased roadmap for integrating Machine Learning where it genuinely adds measurable value.

---

## 2. What Our Current MVP Rules Do

The MVP engine evaluates high-confidence topological and behavioral signals:
- **Temporal Order Constraint ($t_{out} \ge t_{in}$)**: Ensures fund paths follow real chronological forward flow.
- **Turnover Speed / Velocity**: Measures average holding time ($\Delta t$) between incoming and outgoing transfers to identify automated script-driven laundering.
- **Peel-Chain & Fan-Out/Fan-In Detection**: Quantifies fund splitting (1 to many) and consolidation (many to 1) patterns commonly used to evade threshold-based reporting.
- **Pass-Through / Transit Wallet Identification**: Identifies intermediary addresses that retain zero or near-zero balance while immediately forwarding $\ge 90\%$ of received assets.
- **Known VASP Directory Matching**: Matches destination nodes against verified exchange deposit and hot wallet databases.

---

## 3. Why ML Cannot Be Trained Without Reliable Labeled Data

Deploying Supervised ML or Graph Neural Networks (GNNs) in blockchain forensics requires addressing four fundamental realities:

1. **Scarcity of Ground-Truth Labels**: The Ethereum ledger provides addresses and transaction amounts, but no ground-truth identities. Reliable labels (e.g., "confirmed pig-butchering mule wallet" vs. "regular retail trader") exist only inside proprietary commercial intelligence databases (Chainalysis, Elliptic, TRM Labs) or Law Enforcement / FIU case archives.
2. **Extreme Class Imbalance**: Illicit transactions account for less than $0.5\%$ of total global cryptocurrency volume. Naive classifiers suffer from overwhelming false-positive rates.
3. **Adversarial Concept Drift**: Fraudsters actively modify laundering patterns (e.g., switching from single-chain peel chains to cross-chain bridges, decentralized liquidity pools, and batching aggregators). An overfitted model trained on static historical data quickly degrades.
4. **Legal Standards of Evidence**: Indian courts require forensic evidence to be verifiable under Section 65B of the Indian Evidence Act. An investigator must explain *which specific on-chain transactions* constituted the trail, rather than citing a neural network's latent vector score.

---

## 4. Required Datasets & Labels for Future Training

To advance from heuristic scoring to production-grade ML, the following dataset infrastructure is required:

| Asset | Required Source | Purpose |
| :--- | :--- | :--- |
| **Address Entity Labels** | Etherscan tags, Dune Analytics, FIU-IND registries, Exchange proof-of-reserves | Supervised classification of wallet types (Personal EOA, Smart Contract, VASP Deposit, Mixer, Bridge). |
| **Laundering Case Subgraphs** | Anonymized case dossiers from cyber crime cells (FIRs / victim reports) | Benchmark control dataset for true positive multi-hop laundering chains. |
| **Benign Baseline Traces** | Mainnet retail transfers, DEX swaps, NFT trades, staking deposits | Negative control dataset to prevent false positives on legitimate retail traders. |

---

## 5. Phased ML Evolution Roadmap

```
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│       PHASE 1: MVP      │     │  PHASE 2: POST-INTERNAL │     │     PHASE 3: FUTURE     │
│ (Current Hackathon)     │ ──> │ (Heuristic + ML Hybrid) │ ──> │ (Full Graph ML & GNNs)  │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
  • NetworkX MultiDiGraph         • Unsupervised Anomaly          • Temporal GNNs (T-GNN)
  • Time-Constrained Traversal      Detection (Isolation Forest)  • Multi-Asset Relational GNNs
  • Explainable Rule-Score        • Co-spending / Deposit         • Automated Subgraph
  • VASP Exact Match Lookup         Clustering Heuristics           Isomorphism Matching
                                  • LightGBM Wallet Classifier
```

### Phase 1: MVP (Current Implementation)
- Deterministic multi-hop path extraction with cycle prevention and depth pruning.
- Explainable additive rule scoring (0–100) with explicit indicator breakdowns.
- Exact matching against Member 2's known VASP directory.

### Phase 2: Post-Internal (Unsupervised & Tabular ML Hybrid)
- **Unsupervised Anomaly Detection**: Train **Isolation Forests** or **Autoencoders** on the 18+ graph features extracted by `WalletFeatureExtractor` to flag statistical outliers in transaction velocity and counterparty dispersion.
- **Deposit Address Co-clustering**: Implement the *Common-Deposit Heuristic* (wallets sending to the same exchange deposit address are clustered under the same actor).
- **Tabular Wallet Classifier**: Train **LightGBM / XGBoost** on extracted graph features to categorize wallet behavior into: `Retail User`, `Mule Forwarder`, `Consolidator`, `DeFi Bot`.

### Phase 3: Future (Graph Neural Networks & Relational Embeddings)
- **Heterogeneous Graph Neural Networks (RGCN / E-GraphSAGE)**: Learn topological embeddings over multi-token graphs (ETH + ERC-20s + contract calls) to predict unknown exchange clusters.
- **Temporal Graph Networks (TGN)**: Dynamic link prediction that updates node states in real-time as new blocks are mined.
- **Automated Subgraph Pattern Recognition**: Graph isomorphism algorithms to automatically flag complex obfuscation topologies (e.g., circular peeling, layered smurfing networks).
