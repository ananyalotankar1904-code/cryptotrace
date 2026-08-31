import pytest
from typing import Dict, Any


@pytest.fixture
def mock_eth_transfer_raw() -> Dict[str, Any]:
    """Sample raw native ETH transfer from Alchemy Transfers API."""
    return {
        "blockNum": "0x12a05f3",
        "uniqueId": "0x4f8c9b...:external:0",
        "hash": "0x4f8c9b1a23456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "from": "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        "to": "0x742d35cc6634c0532925a3b844bc454e4438f44e",
        "value": 1.25,
        "asset": "ETH",
        "category": "external",
        "rawContract": {
            "value": "0x1158e460913d0000",
            "address": None,
            "decimal": "0x12",
        },
        "metadata": {
            "blockTimestamp": "2024-03-15T14:30:00.000Z"
        },
    }


@pytest.fixture
def mock_erc20_transfer_raw() -> Dict[str, Any]:
    """Sample raw ERC-20 USDT token transfer from Alchemy Transfers API."""
    return {
        "blockNum": "0x12a0610",
        "uniqueId": "0x987654...:erc20:log_12",
        "hash": "0x9876543210abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "from": "0x742d35cc6634c0532925a3b844bc454e4438f44e",
        "to": "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        "value": 5000.0,
        "asset": "USDT",
        "category": "erc20",
        "rawContract": {
            "value": "0x12a05f200",
            "address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
            "decimal": "0x6",
        },
        "metadata": {
            "blockTimestamp": "2024-03-15T14:35:12.000Z"
        },
    }


@pytest.fixture
def mock_alchemy_rpc_response(mock_eth_transfer_raw, mock_erc20_transfer_raw) -> Dict[str, Any]:
    """Sample complete Alchemy JSON-RPC successful response."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "transfers": [
                mock_eth_transfer_raw,
                mock_erc20_transfer_raw,
            ],
            "pageKey": "01234567-89ab-cdef-0123-456789abcdef",
        },
    }


@pytest.fixture
def mock_empty_rpc_response() -> Dict[str, Any]:
    """Sample Alchemy response for wallet with 0 transactions."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "transfers": [],
            "pageKey": None,
        },
    }
