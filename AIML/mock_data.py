"""
Mock Dataset for Testing and Frontend Integration
Project: Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges
Role: AI/ML + Graph Analytics Layer

NOTE: All addresses, transaction hashes, and entities below are SYNTHETIC MOCK DATA
designed solely for unit testing, pipeline verification, and UI visualization.
"""

from typing import Dict, List, Any


# Synthetic Wallets:
# A: Suspect Root (0xMOCK_SUSPECT_A0000000000000000000000000000)
# B: Intermediary 1 (0xMOCK_INTERMEDIARY_B11111111111111111111111)
# C: Intermediary 2 (0xMOCK_INTERMEDIARY_C22222222222222222222222)
# D: Mule Forwarder (0xMOCK_MULE_D33333333333333333333333333333333)
# E: Cold Wallet (0xMOCK_COLD_E44444444444444444444444444444444444)
# F: Known VASP Deposit (0xMOCK_VASP_BINANCE_F5555555555555555555555)

MOCK_ROOT_WALLET = "0xMOCK_SUSPECT_A0000000000000000000000000000"

# Mock VASP Intelligence Dataset (Simulating Member 2's dataset)
MOCK_VASP_DIRECTORY: Dict[str, Dict[str, Any]] = {
    "0xmock_vasp_binance_f5555555555555555555555": {
        "entity": "Binance",
        "entity_type": "KNOWN_VASP",
        "blockchain": "ethereum",
        "address_type": "deposit_hot_wallet",
        "confidence": "VERIFIED_OFFICIAL",
        "source": "Etherscan Public Label"
    },
    "0xmock_vasp_wazirx_w9999999999999999999999": {
        "entity": "WazirX",
        "entity_type": "KNOWN_VASP",
        "blockchain": "ethereum",
        "address_type": "exchange_cluster",
        "confidence": "VERIFIED_OFFICIAL",
        "source": "FIU Registry"
    }
}

# Synthetic Transfers Dataset matching Member 4 / Alchemy normalized JSON
MOCK_TRANSFERS: List[Dict[str, Any]] = [
    # 1. A -> B : 2.5 ETH (Hop 1)
    {
        "transaction_hash": "0xmock_tx_001_a_to_b_eth",
        "from_address": "0xMOCK_SUSPECT_A0000000000000000000000000000",
        "to_address": "0xMOCK_INTERMEDIARY_B11111111111111111111111",
        "asset": "ETH",
        "value": 2.5,
        "block_number": "19000001",
        "timestamp": "2026-08-30T10:00:00Z",
        "category": "external",
        "contract_address": None,
        "hop": 1
    },
    # 2. A -> B : 1000 USDT (ERC-20 transfer between same pair, multiple transactions)
    {
        "transaction_hash": "0xmock_tx_002_a_to_b_usdt",
        "from_address": "0xMOCK_SUSPECT_A0000000000000000000000000000",
        "to_address": "0xMOCK_INTERMEDIARY_B11111111111111111111111",
        "asset": "USDT",
        "value": 1000.0,
        "block_number": "19000002",
        "timestamp": "2026-08-30T10:05:00Z",
        "category": "erc20",
        "contract_address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "hop": 1
    },
    # 3. A -> C : 1.0 ETH (Branching / Splitting, Hop 1)
    {
        "transaction_hash": "0xmock_tx_003_a_to_c_eth",
        "from_address": "0xMOCK_SUSPECT_A0000000000000000000000000000",
        "to_address": "0xMOCK_INTERMEDIARY_C22222222222222222222222",
        "asset": "ETH",
        "value": 1.0,
        "block_number": "19000003",
        "timestamp": "2026-08-30T10:10:00Z",
        "category": "external",
        "contract_address": None,
        "hop": 1
    },
    # 4. B -> D : 2.4 ETH (Forwarding / Peel, Hop 2)
    {
        "transaction_hash": "0xmock_tx_004_b_to_d_eth",
        "from_address": "0xMOCK_INTERMEDIARY_B11111111111111111111111",
        "to_address": "0xMOCK_MULE_D33333333333333333333333333333333",
        "asset": "ETH",
        "value": 2.4,
        "block_number": "19000010",
        "timestamp": "2026-08-30T10:20:00Z",
        "category": "external",
        "contract_address": None,
        "hop": 2
    },
    # 5. B -> E : 0.08 ETH (Small secondary peel to cold storage, Hop 2)
    {
        "transaction_hash": "0xmock_tx_005_b_to_e_eth",
        "from_address": "0xMOCK_INTERMEDIARY_B11111111111111111111111",
        "to_address": "0xMOCK_COLD_E44444444444444444444444444444444444",
        "asset": "ETH",
        "value": 0.08,
        "block_number": "19000011",
        "timestamp": "2026-08-30T10:22:00Z",
        "category": "external",
        "contract_address": None,
        "hop": 2
    },
    # 6. D -> F : 2.35 ETH (Exit transfer to Known VASP - Binance, Hop 3)
    {
        "transaction_hash": "0xmock_tx_006_d_to_f_binance_eth",
        "from_address": "0xMOCK_MULE_D33333333333333333333333333333333",
        "to_address": "0xMOCK_VASP_BINANCE_F5555555555555555555555",
        "asset": "ETH",
        "value": 2.35,
        "block_number": "19000025",
        "timestamp": "2026-08-30T10:45:00Z",
        "category": "external",
        "contract_address": None,
        "hop": 3
    }
]
