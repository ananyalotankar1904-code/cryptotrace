"""Multi-hop fund-flow tracing service using Breadth-First Search (BFS)."""

import logging
from collections import deque
from typing import List, Optional, Set, Tuple

from app.config import Settings, get_settings
from app.models.transfer import TransferDirection, TransferCategory
from app.models.trace import TracePathItem, TraceSummary, TraceResponse
from app.services.alchemy import (
    AlchemyService,
    AlchemyError,
    AlchemyConfigError,
    AlchemyAuthError,
    AlchemyRateLimitError,
    AlchemyNetworkError,
)

logger = logging.getLogger(__name__)

# Known burn and zero addresses that terminate transaction trails
SPECIAL_TERMINAL_ADDRESSES: Set[str] = {
    "0x0000000000000000000000000000000000000000",
    "0x000000000000000000000000000000000000dead",
    "0x0000000000000000000000000000000000000001",
}


class MultiHopTracer:
    """
    Breadth-First Search (BFS) engine for tracing outgoing fund flows across Ethereum addresses.

    Guarantees loop/cycle prevention, handles native ETH and ERC-20 tokens, distinguishes
    special contract destinations, and enforces strict API rate limits and depth cutoffs.
    """

    def __init__(
        self,
        alchemy_service: Optional[AlchemyService] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.alchemy_service = alchemy_service or AlchemyService(settings=self.settings)

    def _is_special_destination(self, to_address: Optional[str], contract_address: Optional[str]) -> bool:
        """Check if destination is a contract creation (None), burn address, or token self-contract."""
        if to_address is None:
            return True
        norm_to = to_address.lower()
        if norm_to in SPECIAL_TERMINAL_ADDRESSES:
            return True
        if contract_address and norm_to == contract_address.lower():
            return True
        return False

    async def trace_wallet(
        self,
        root_address: str,
        max_depth: Optional[int] = None,
        max_transfers_per_wallet: Optional[int] = None,
        categories: Optional[List[str]] = None,
    ) -> TraceResponse:
        """
        Execute BFS multi-hop fund-flow tracing starting from `root_address`.

        Args:
            root_address: Validated, normalized lowercase Ethereum address.
            max_depth: Maximum hop traversal depth (default 3, clamped to 1..MAX_DEPTH_LIMIT).
            max_transfers_per_wallet: Outgoing transfers fetched per wallet (clamped to 1..MAX_TRANSFERS_LIMIT).
            categories: List of transfer categories (defaults to ['external', 'erc20']).

        Returns:
            TraceResponse containing discovered paths, summary metrics, and safety warnings.
        """
        # 1. Clamp and validate traversal configuration
        clamped_depth = max(
            1,
            min(
                max_depth if max_depth is not None else self.settings.DEFAULT_MAX_DEPTH,
                self.settings.MAX_DEPTH_LIMIT,
            ),
        )
        clamped_max_transfers = max(
            1,
            min(
                max_transfers_per_wallet
                if max_transfers_per_wallet is not None
                else self.settings.DEFAULT_MAX_TRANSFERS_PER_WALLET,
                self.settings.MAX_TRANSFERS_PER_WALLET_LIMIT,
            ),
        )
        if categories is None or not categories:
            categories = [TransferCategory.EXTERNAL.value, TransferCategory.ERC20.value]

        norm_root = root_address.strip().lower()

        # 2. Initialize BFS tracking structures
        # FIFO queue holds tuples of (wallet_address, current_hop_depth)
        queue: deque[Tuple[str, int]] = deque([(norm_root, 0)])
        
        # Visited addresses: prevents duplicate outgoing queries and eliminates infinite cycles (A -> B -> A)
        visited_addresses: Set[str] = {norm_root}
        
        # Discovered addresses: all unique Ethereum addresses encountered as source or target
        discovered_addresses: Set[str] = {norm_root}
        
        # Discovered transfer paths (edges)
        paths: List[TracePathItem] = []
        
        # Deduplication keys for transfers to avoid recording identical events multiple times
        seen_transfer_keys: Set[str] = set()
        
        warnings: List[str] = []
        pagination_occurred = False
        wallets_queried = 0

        # 3. BFS Traversal Loop
        while queue:
            current_wallet, current_depth = queue.popleft()

            # If current wallet depth has reached max_depth, do not expand further outgoing transfers
            if current_depth >= clamped_depth:
                continue

            # Circuit breaker: check if maximum wallet query ceiling has been reached
            if wallets_queried >= self.settings.MAX_TOTAL_WALLETS_TRACED:
                limit_msg = (
                    f"Safety cutoff: Maximum wallet limit ({self.settings.MAX_TOTAL_WALLETS_TRACED}) "
                    "reached. Terminated further BFS expansion."
                )
                if limit_msg not in warnings:
                    warnings.append(limit_msg)
                break

            # Fetch outgoing transfers for current wallet
            try:
                transfer_response = await self.alchemy_service.get_wallet_transfers(
                    address=current_wallet,
                    direction=TransferDirection.FROM,
                    categories=categories,
                    max_count=clamped_max_transfers,
                )
                wallets_queried += 1
            except (AlchemyAuthError, AlchemyConfigError, AlchemyRateLimitError, AlchemyNetworkError) as err:
                # Fatal Alchemy infrastructure / auth / rate limit errors must bubble up
                raise err
            except AlchemyError as err:
                if current_wallet == norm_root:
                    raise err
                logger.warning(f"Alchemy error querying downstream wallet {current_wallet}: {err.message}")
                warnings.append(f"Skipped downstream wallet {current_wallet}: {err.message}")
                continue
            except Exception as exc:
                if current_wallet == norm_root:
                    raise exc
                logger.warning(f"Error querying transfers for wallet {current_wallet}: {exc}")
                warnings.append(f"Failed to fetch transfers for wallet {current_wallet}: {str(exc)}")
                continue

            if transfer_response.page_key is not None:
                pagination_occurred = True
                warnings.append(
                    f"Wallet {current_wallet} has additional outgoing transfers beyond the "
                    f"per-wallet limit of {clamped_max_transfers}."
                )

            hop_number = current_depth + 1

            for transfer in transfer_response.transfers:
                to_addr = transfer.to_address.lower() if transfer.to_address else None
                from_addr = transfer.from_address.lower()

                # Determine if the destination is a special terminal address or smart contract
                is_contract = self._is_special_destination(to_addr, transfer.contract_address)

                # Deduplication key for this transfer edge
                transfer_key = (
                    transfer.unique_id
                    or f"{transfer.transaction_hash}:{transfer.category}:{from_addr}:{to_addr}:{transfer.value}:{transfer.block_number}"
                )

                if transfer_key not in seen_transfer_keys:
                    seen_transfer_keys.add(transfer_key)

                    path_item = TracePathItem(
                        from_address=from_addr,
                        to_address=to_addr,
                        asset=transfer.asset,
                        value=transfer.value,
                        transaction_hash=transfer.transaction_hash,
                        block_number=transfer.block_number,
                        timestamp=transfer.timestamp,
                        category=transfer.category,
                        contract_address=transfer.contract_address,
                        hop=hop_number,
                        is_contract_destination=is_contract if to_addr else True,
                    )
                    paths.append(path_item)

                # Record discovered unique addresses
                discovered_addresses.add(from_addr)
                if to_addr:
                    discovered_addresses.add(to_addr)

                # Enqueue valid destination for next hop if:
                # 1. to_addr is not null and not a terminal/burn contract
                # 2. to_addr has not been visited yet (cycle/loop prevention)
                # 3. Next hop depth does not exceed max_depth
                if to_addr and not is_contract:
                    if to_addr not in visited_addresses and hop_number < clamped_depth:
                        visited_addresses.add(to_addr)
                        queue.append((to_addr, hop_number))

        # 4. Compute Forensic Summary Metrics
        max_hop_reached = max((p.hop for p in paths), default=0)
        network_name = (
            "mainnet"
            if "mainnet" in self.settings.ALCHEMY_NETWORK
            else self.settings.ALCHEMY_NETWORK
        )

        summary = TraceSummary(
            root_wallet=norm_root,
            unique_addresses_discovered=len(discovered_addresses),
            transfers_analyzed=len(paths),
            max_hop_reached=max_hop_reached,
            total_paths=len(paths),
            pagination_occurred=pagination_occurred,
            wallets_queried=wallets_queried,
            warnings=warnings,
        )

        return TraceResponse(
            root_wallet=norm_root,
            blockchain="ethereum",
            network=network_name,
            max_depth=clamped_depth,
            summary=summary,
            paths=paths,
        )
