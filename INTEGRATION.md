# Backend & AIML Integration

This document describes the integration between the FastAPI backend and the AI/ML analytics layer.

## Architecture & Data Flow

The integration implements a clean pipeline where the backend orchestrates the execution while offloading complex graph calculations to the AIML service. 

**Data Flow:**
1. **Wallet Address Input:** User provides an Ethereum address via `GET /wallet/{address}/analyze`.
2. **Backend Validation:** The FastAPI backend validates the address formatting.
3. **Alchemy Retrieval & Tracing:** The `MultiHopTracer` (backend) connects to Alchemy, fetching transfers and exploring outgoing hops up to `max_depth`.
4. **Analytics Handoff:** The normalized trace paths are passed directly into the `analyze_transaction_graph` function in the AIML analytics module (`backend/app/services/analytics`).
5. **Graph & Risk Computation:** The AIML module builds the multi-hop graph, extracts wallet-level behavioral features, and computes the rule-based risk score.
6. **Combined Response:** The backend merges the tracing topology and AIML outputs into a single JSON `CombinedAnalysisResponse`.

## Responsibilities

### Backend (`app.routes`, `app.services.alchemy`, `app.services.tracer`)
- Web server and endpoint routing.
- Input validation.
- Securely handling Alchemy API keys via environment variables.
- Fetching and paginating native ETH and ERC-20 transfers.
- Executing Breadth-First Search (BFS) graph discovery to prevent infinite loops.

### Analytics Layer (`app.services.analytics`)
- Taking raw transaction connections (Trace paths) to construct a NetworkX graph.
- Deriving entity-level features (e.g. transfer velocity, total volume out, path consolidation).
- Assessing fraud risk based on rules.
- Providing frontend-friendly node/edge structures.
- Correlating with VASP datasets (when enabled).

## Input & Output Schemas

**Analytics Input (List of Dicts):**
The analytics layer receives a list of normalized transfer dicts mimicking the `TracePathItem` structure:
```json
{
  "from": "0xA...",
  "to": "0xB...",
  "asset": "ETH",
  "value": 0.5,
  "transaction_hash": "0x...",
  "block_number": 123456,
  "timestamp": "2026-08-30T10:00:00Z",
  "category": "external",
  "contract_address": null,
  "hop": 1
}
```

**Analytics Output (Dict):**
```json
{
  "root_wallet": "0x...",
  "wallet_count": 12,
  "transaction_count": 25,
  "max_hop": 3,
  "risk_score": 72,
  "risk_level": "HIGH",
  "risk_indicators": ["Rapid successive transfers"],
  "known_entities": [],
  "nodes": [...],
  "edges": [...],
  "paths": [...],
  ...
}
```

## Known Limitations
- The AIML risk scorer is currently purely rule-based.
- Performance may degrade with extremely high `max_depth` due to rate limits and large graph construction overhead.
- Only external (ETH) and ERC-20 transfers are supported in the core flow.

## Future VASP Integration
Member 2's VASP Intelligence dataset has an open integration point in the `analyze_transaction_graph` function (`vasp_directory` parameter). In the future, the global VASP map will be provided during service initialization to automatically flag known exchanges and entities within the trace graph.
