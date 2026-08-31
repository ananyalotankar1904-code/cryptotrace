"""Multi-hop trace models and schemas for structured fund-flow responses."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TracePathItem(BaseModel):
    """
    Representation of a single directed fund transfer hop along a multi-hop trail.

    Uses 'from' and 'to' aliases to match standard forensic graph specifications.
    """

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    from_address: str = Field(
        ...,
        alias="from",
        serialization_alias="from",
        description="Source wallet or contract address for this hop.",
    )
    to_address: Optional[str] = Field(
        default=None,
        alias="to",
        serialization_alias="to",
        description="Destination wallet or contract address for this hop (null if contract creation).",
    )
    asset: Optional[str] = Field(
        default=None,
        description="Asset symbol transferred (e.g., 'ETH', 'USDT', 'DAI').",
    )
    value: Optional[float] = Field(
        default=None,
        description="Human-readable amount transferred (normalized by decimals for tokens).",
    )
    transaction_hash: str = Field(
        ...,
        description="On-chain Ethereum transaction hash (0x...).",
    )
    block_number: int = Field(
        ...,
        description="Ethereum block number where the transaction was mined.",
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="ISO-8601 UTC timestamp of the block if available.",
    )
    category: str = Field(
        ...,
        description="Transfer category: 'external' (native ETH), 'erc20' (fungible token), etc.",
    )
    contract_address: Optional[str] = Field(
        default=None,
        description="Smart contract address for token transfers (null for native ETH).",
    )
    hop: int = Field(
        ...,
        description="Hop distance from the root wallet (1 for direct outgoing, 2 for second hop, etc.).",
    )
    is_contract_destination: Optional[bool] = Field(
        default=None,
        description="Flag indicating if the destination address is a known smart contract or burn address.",
    )


class TraceSummary(BaseModel):
    """Forensic summary metrics for a multi-hop trace execution."""

    root_wallet: str = Field(
        description="Starting suspect wallet address for the multi-hop trace.",
    )
    unique_addresses_discovered: int = Field(
        description="Total count of unique Ethereum addresses encountered across all hops.",
    )
    transfers_analyzed: int = Field(
        description="Total number of outgoing transfer records evaluated in the trace.",
    )
    max_hop_reached: int = Field(
        description="Maximum hop distance reached during the traversal.",
    )
    total_paths: int = Field(
        description="Total number of directed transfer hops (edges) recorded.",
    )
    pagination_occurred: bool = Field(
        default=False,
        description="True if any queried wallet had more transfers than the per-wallet retrieval limit.",
    )
    wallets_queried: int = Field(
        default=0,
        description="Number of distinct wallets whose outgoing transfers were queried.",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of informational notices or safety limit cutoffs encountered during tracing.",
    )


class TraceResponse(BaseModel):
    """Complete standardized response for a multi-hop fund-flow trace."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    root_wallet: str = Field(
        description="Starting suspect wallet address."
    )
    blockchain: str = Field(
        default="ethereum",
        description="Target blockchain ecosystem (default: ethereum).",
    )
    network: str = Field(
        default="mainnet",
        description="Blockchain network name (e.g. mainnet, sepolia).",
    )
    max_depth: int = Field(
        description="Maximum hop depth requested for the trace.",
    )
    summary: TraceSummary = Field(
        description="High-level forensic analytics and traversal summary.",
    )
    paths: List[TracePathItem] = Field(
        default_factory=list,
        description="Chronologically structured list of discovered transfer hops.",
    )
