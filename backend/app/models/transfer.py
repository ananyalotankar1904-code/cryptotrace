"""Transfer models and schemas for structured responses."""

from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class TransferCategory(str, Enum):
    """Supported Alchemy transfer categories."""

    EXTERNAL = "external"
    INTERNAL = "internal"
    ERC20 = "erc20"
    ERC721 = "erc721"
    ERC1155 = "erc1155"
    SPECIALNFT = "specialnft"


class TransferDirection(str, Enum):
    """Filter transfers by direction relative to the target address."""

    ALL = "all"
    FROM = "from"
    TO = "to"


class RawContractInfo(BaseModel):
    """Raw contract metadata returned by Alchemy API for deep forensic checks."""

    address: Optional[str] = Field(
        default=None,
        description="Smart contract address for token/NFT transfers.",
    )
    value: Optional[str] = Field(
        default=None,
        description="Hex-encoded or raw integer string of the transfer value in smallest unit (e.g., wei).",
    )
    decimal: Optional[str] = Field(
        default=None,
        description="Hex-encoded or integer string representing token decimal precision.",
    )


class TransferItem(BaseModel):
    """
    Clean, normalized representation of an on-chain asset transfer.
    
    Explicitly distinguishes native ETH transfers (external) from token transfers (ERC-20).
    """

    transaction_hash: str = Field(
        description="On-chain Ethereum transaction hash (0x...)."
    )
    from_address: str = Field(
        description="Source wallet or smart contract address."
    )
    to_address: Optional[str] = Field(
        default=None,
        description="Destination wallet or smart contract address (None if contract creation).",
    )
    asset: Optional[str] = Field(
        default=None,
        description="Asset symbol (e.g. 'ETH', 'USDT', 'USDC', 'DAI').",
    )
    value: Optional[float] = Field(
        default=None,
        description="Human-readable transferred amount normalized by token decimals.",
    )
    block_number: int = Field(
        description="Block number where the transaction was mined (as an integer).",
    )
    category: str = Field(
        description="Transfer category: 'external' (native ETH), 'erc20' (fungible token), etc.",
    )
    contract_address: Optional[str] = Field(
        default=None,
        description="Smart contract address (populated for ERC-20 token transfers, null for native ETH).",
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="ISO-8601 UTC timestamp of the block when available from Alchemy metadata.",
    )
    unique_id: Optional[str] = Field(
        default=None,
        description="Alchemy unique identifier for this transfer event log.",
    )
    raw_contract: Optional[RawContractInfo] = Field(
        default=None,
        description="Preserved raw contract and decimal information for deep forensic verification.",
    )


class TransferResponse(BaseModel):
    """Standardized API response for wallet transfer queries across the SIH analytics pipeline."""

    wallet_address: str = Field(
        description="The Ethereum wallet address queried."
    )
    blockchain: str = Field(
        default="ethereum",
        description="Target blockchain platform (default: ethereum).",
    )
    network: str = Field(
        default="mainnet",
        description="Blockchain network name (e.g., mainnet, sepolia).",
    )
    direction: str = Field(
        default="all",
        description="Query direction applied ('all', 'from', or 'to').",
    )
    transfer_count: int = Field(
        description="Total number of transfer items returned in the current page.",
    )
    page_key: Optional[str] = Field(
        default=None,
        description="Pagination cursor token to fetch the subsequent page of transfers (null if no more records).",
    )
    transfers: List[TransferItem] = Field(
        default_factory=list,
        description="List of structured, normalized asset transfer items sorted chronologically (newest first).",
    )


class ErrorResponse(BaseModel):
    """Standardized error response model."""

    error: str = Field(description="Short error code or category.")
    message: str = Field(description="Human-readable description of the error.")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional additional error context (never exposes API keys or secrets).",
    )
