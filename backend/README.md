# SIH Crypto Fraud Intelligence Engine - Backend Data Layer

> **Project:** Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges from Victim-Reported Suspect Wallet Addresses through Automated Blockchain Analytics  
> **Milestone 2:** Clean Normalized JSON Data Layer & Transformation Engine  
> **Milestone 3:** Basic Multi-Hop Fund-Flow Tracing (Breadth-First Search)

---

## 1. System Overview & Multi-Hop Pipeline Flow

The engine enables law enforcement and forensic investigators to input a victim-reported suspect Ethereum wallet address and trace the movement of funds across multiple transaction hops.

```
Victim / Investigator Input: Suspect Wallet Address (0x...)
                            │
                            ▼
           Address Validation & Normalization
                            │
                            ▼
              Multi-Hop BFS Tracing Engine
        (Breadth-First Search with Loop Prevention)
                            │
 ┌──────────────────────────┴──────────────────────────┐
 │                                                     │
 ▼ (Hop 1)                                             ▼ (Hop 2 ... Hop N)
Root Wallet Outgoing Transfers                  Child Destination Outgoing Transfers
(direction = FROM)                              (direction = FROM)
 │                                                     │
 └──────────────────────────┬──────────────────────────┘
                            │
                            ▼
              Alchemy Transfers API Layer
       (`alchemy_getAssetTransfers` JSON-RPC)
                            │
                            ▼
           Normalization & Deduplication Layer
   (Native ETH vs Decimals-Normalized ERC-20 Tokens)
                            │
                            ▼
       STRUCTURED MULTI-HOP FUND-FLOW RESPONSE
   (Directed Path Graph, Hop Distances, Forensic Summary)
```

---

## 2. API Endpoints Specification

### 2.1 Multi-Hop Fund-Flow Tracing
**`GET /wallet/{address}/trace`**

Recursively traces outgoing fund transfers from a suspect wallet across multiple hops using Breadth-First Search (BFS).

#### Parameters:
| Parameter | Location | Type | Default | Constraints | Description |
|---|---|---|---|---|---|
| `address` | Path | `string` | *Required* | 42-char Hex | Starting suspect Ethereum address (`0x...`). |
| `max_depth` | Query | `integer` | `3` | `1` to `5` | Maximum traversal depth / hop distance. |
| `max_transfers_per_wallet` | Query | `integer` | `25` | `1` to `100` | Max outgoing transfers analyzed per wallet node. |
| `categories` | Query | `string` | `external,erc20` | Comma-separated | Categories: `external` (native ETH), `erc20` (tokens), `internal`. |

---

### 2.2 Single Wallet Transfer Retrieval
**`GET /wallet/{address}/transfers`**

Retrieves normalized historical asset transfers for a single address.

#### Parameters:
| Parameter | Location | Type | Default | Description |
|---|---|---|---|---|
| `address` | Path | `string` | *Required* | 42-character hexadecimal Ethereum address (`0x...`). |
| `direction` | Query | `string` | `all` | `all` (incoming + outgoing), `from` (outgoing only), `to` (incoming only). |
| `categories` | Query | `string` | `external,erc20` | Comma-separated transfer categories. |
| `max_count` | Query | `integer` | `100` | Max items returned per page (1 to 1000). |
| `page_key` | Query | `string` | `null` | Pagination cursor key. |

---

### 2.3 Integrated Graph Analytics & Risk Analysis
**`GET /wallet/{address}/analyze`**

Retrieves multi-hop transfers and passes them to the integrated AIML layer to generate a transaction graph, extract entity features, compute an explainable risk score, and format a combined JSON response.

#### Parameters:
| Parameter | Location | Type | Default | Description |
|---|---|---|---|---|
| `address` | Path | `string` | *Required* | 42-character hexadecimal Ethereum address (`0x...`). |
| `max_depth` | Query | `integer` | `3` | Maximum hop depth for tracing (1 to 5). |
| `max_transfers_per_wallet` | Query | `integer` | `25` | Max outgoing transfers analyzed per wallet. |

---

## 3. Multi-Hop Tracing Logic & Architecture

### 3.1 Meaning of a "Hop"
- **Hop 0:** The root suspect wallet $A$.
- **Hop 1:** Direct outgoing transfers from the root wallet ($A \to B$, $A \to C$).
- **Hop 2:** Direct outgoing transfers from Hop 1 destinations ($B \to D$, $C \to E$).
- **Hop 3:** Subsequent outgoing transfers ($D \to F$, $E \to G$).

### 3.2 Breadth-First Search (BFS) Traversal
BFS processes all Hop 1 transactions before advancing to Hop 2, ensuring that the closest transaction relationships are established first:
1. Initialize FIFO queue: `[(root_wallet, depth=0)]`.
2. Maintain `visited_addresses: Set[str]` initialized with `{root_wallet}`.
3. Dequeue `(current_wallet, current_depth)`.
4. If `current_depth >= max_depth`: Stop expanding that branch.
5. Query outgoing transfers (`direction=FROM`) for `current_wallet`.
6. For each transfer to `destination`:
   - Record the directed path edge with `hop = current_depth + 1`.
   - If `destination` has not been visited and is not a contract/burn address:
     - Add `destination` to `visited_addresses`.
     - Enqueue `(destination, current_depth + 1)`.

### 3.3 Cycle & Loop Prevention
If a recipient sends funds back to a previously visited wallet (e.g. $A \to B \to A$ or a circular ring $A \to B \to C \to B$):
- The edge $B \to A$ is recorded as a valid Hop 2 path relationship.
- However, because $A \in \text{visited\_addresses}$, $A$ is **never enqueued again**.
- This guarantees termination and completely eliminates infinite loops.

### 3.4 Handling Contracts & Terminal Addresses
- Transfers to burn addresses (`0x0000000000000000000000000000000000000000`, `0x...dead`), contract creations (`to = null`), or interactions directly with token contracts are preserved in `paths` with `is_contract_destination: true`, but are **not** enqueued for outgoing traversal.

### 3.5 Rate Limits & Safety Circuit Breakers
To safeguard against exponential explosion and respect Alchemy API quotas:
- `MAX_DEPTH`: Capped at `5` (default `3`).
- `MAX_TRANSFERS_PER_WALLET`: Capped at `100` (default `25`).
- `MAX_TOTAL_WALLETS_TRACED`: Hard circuit breaker at `50` wallets per trace.
- When pagination occurs (wallet has more transfers than `max_transfers_per_wallet`), `pagination_occurred: true` is flagged and recorded in `summary.warnings`.

---

## 4. Fundamental Blockchain Logic & Fund Continuity Disclaimer

> [!IMPORTANT]
> **Multi-Hop Traversal Traces Transaction Relationships, Not Mathematical Coin Continuity.**
> 
> In account-based blockchains like Ethereum:
> 1. Tracing an edge $A \to B \to C$ proves that wallet $A$ sent assets to $B$, and wallet $B$ subsequently or previously sent assets to $C$.
> 2. It does **not** prove that the exact same wei/tokens received from $A$ were transferred to $C$. Wallet $B$ may have held pre-existing balances, commingled funds from multiple sources, or executed transfers at unrelated times.
> 3. Native ETH and ERC-20 tokens are tracked independently. Token amounts are computed from contract event logs and normalized by token decimal precision, whereas ETH transfers represent native EVM value transfers.

---

## 5. Example API Response (`GET /wallet/{address}/trace`)

```json
{
  "root_wallet": "0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503",
  "blockchain": "ethereum",
  "network": "mainnet",
  "max_depth": 3,
  "summary": {
    "root_wallet": "0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503",
    "unique_addresses_discovered": 11,
    "transfers_analyzed": 11,
    "max_hop_reached": 3,
    "total_paths": 11,
    "pagination_occurred": true,
    "wallets_queried": 7,
    "warnings": [
      "Wallet 0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503 has additional outgoing transfers beyond the per-wallet limit of 2."
    ]
  },
  "paths": [
    {
      "from": "0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503",
      "to": "0xf977814e90da44bfa03b6295a0616a897441acec",
      "asset": "DAI",
      "value": 30000000.0,
      "transaction_hash": "0x2e46c5a5fd5b52f66a0b7d97998a70cfefd5ce944e999fe5ac296a1a0a171f20",
      "block_number": 12558746,
      "timestamp": "2021-06-03T02:04:05.000Z",
      "category": "erc20",
      "contract_address": "0x6b175474e89094c44da98b954eedeac495271d0f",
      "hop": 1,
      "is_contract_destination": false
    },
    {
      "from": "0xf977814e90da44bfa03b6295a0616a897441acec",
      "to": "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be",
      "asset": "MFT",
      "value": 70000000.0,
      "transaction_hash": "0x9fc4f7d1b04013cf82f5b5c65178ff5135c2a8c48d8a70f292754637df460528",
      "block_number": 8117731,
      "timestamp": "2019-07-09T14:54:02.000Z",
      "category": "erc20",
      "contract_address": "0xdf2c7238198ad8b389666574f2d8bc411a4b7428",
      "hop": 2,
      "is_contract_destination": false
    },
    {
      "from": "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be",
      "to": "0x001866ae5b3de6caa5a51543fd9fb64f524f5478",
      "asset": "ETH",
      "value": 0.045,
      "transaction_hash": "0xd7be6ba52109ce95c102a905a415ff5e0f7f329971db4106518174f884fbf35c",
      "block_number": 4116404,
      "timestamp": null,
      "category": "external",
      "contract_address": null,
      "hop": 3,
      "is_contract_destination": false
    }
  ]
}
```

---

## 6. Live Ethereum Mainnet Test Verification

The table below illustrates verified multi-hop transaction paths extracted from Ethereum Mainnet:

| Hop | Source Address (`from`) | Destination Address (`to`) | Asset | Transferred Value | Block | Etherscan Transaction Link |
|---|---|---|---|---|---|---|
| **1** | `0x47ac...d503` | `0xf977...acec` | `DAI` | `30,000,000.0` | `12558746` | [`0x2e46c5a5...`](https://etherscan.io/tx/0x2e46c5a5fd5b52f66a0b7d97998a70cfefd5ce944e999fe5ac296a1a0a171f20) |
| **1** | `0x47ac...d503` | `0x6b17...1d0f` | `ETH` | `0.0` | `12558746` | [`0x2e46c5a5...`](https://etherscan.io/tx/0x2e46c5a5fd5b52f66a0b7d97998a70cfefd5ce944e999fe5ac296a1a0a171f20) |
| **2** | `0xf977...acec` | `0x3f5c...f0be` | `MFT` | `70,000,000.0` | `8117731` | [`0x9fc4f7d1...`](https://etherscan.io/tx/0x9fc4f7d1b04013cf82f5b5c65178ff5135c2a8c48d8a70f292754637df460528) |
| **2** | `0x6b17...1d0f` | `0xc449...07b4` | `daiblack.com` | `100.0` | `15447682` | [`0x31f60d79...`](https://etherscan.io/tx/0x31f60d794bbcb297a7c8ab1235b555fd03465ebf0a70b34875bc3701a55f5f6f) |
| **3** | `0x3f5c...f0be` | `0x0018...5478` | `ETH` | `0.045` | `4116404` | [`0xd7be6ba5...`](https://etherscan.io/tx/0xd7be6ba52109ce95c102a905a415ff5e0f7f329971db4106518174f884fbf35c) |
| **3** | `0xed76...764b` | `0x5777...2168` | `USDC` | `24,948.96` | `15416716` | [`0x902ff3a2...`](https://etherscan.io/tx/0x902ff3a220cfc388bc3b890ce5d3dc68b0669ecbdf11f26a8d8e578c78c3b4cf) |

---

## 7. Running the Service & Automated Tests

```powershell
# Start FastAPI backend server
.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Run complete automated test suite (25/25 passing)
.venv\Scripts\pytest -v
```
