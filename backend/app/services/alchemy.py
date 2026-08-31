import asyncio
import logging
from typing import List, Optional, Dict, Any, Tuple
import httpx

from app.config import Settings, get_settings
from app.models.transfer import (
    TransferCategory,
    TransferDirection,
    RawContractInfo,
    TransferItem,
    TransferResponse,
)

logger = logging.getLogger(__name__)


class AlchemyError(Exception):
    """Base exception for Alchemy service errors."""

    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class AlchemyConfigError(AlchemyError):
    """Raised when the Alchemy API key is missing or not configured."""

    def __init__(self, message: str = "Alchemy API key is not configured in .env file."):
        super().__init__(message=message, status_code=500)


class AlchemyAuthError(AlchemyError):
    """Raised when Alchemy authentication fails (invalid or unauthorized key)."""

    def __init__(self, message: str = "Alchemy authentication failed: Invalid API key."):
        super().__init__(message=message, status_code=502)


class AlchemyRateLimitError(AlchemyError):
    """Raised when Alchemy rate limit is encountered (HTTP 429)."""

    def __init__(self, message: str = "Alchemy API rate limit exceeded. Please try again later."):
        super().__init__(message=message, status_code=429)


class AlchemyNetworkError(AlchemyError):
    """Raised when network failure or timeout occurs while reaching Alchemy."""

    def __init__(self, message: str = "Failed to communicate with Alchemy API due to network timeout/error."):
        super().__init__(message=message, status_code=504)


class AlchemyService:
    """Service to interact with Alchemy Transfers API and parse Ethereum asset transfers."""

    def __init__(self, settings: Optional[Settings] = None, client: Optional[httpx.AsyncClient] = None):
        self.settings = settings or get_settings()
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None and not self._client.is_closed:
            return self._client
        return httpx.AsyncClient(timeout=self.settings.REQUEST_TIMEOUT_SECONDS)

    def _build_jsonrpc_payload(
        self,
        from_address: Optional[str] = None,
        to_address: Optional[str] = None,
        categories: Optional[List[str]] = None,
        max_count: int = 100,
        page_key: Optional[str] = None,
        from_block: str = "0x0",
        to_block: str = "latest",
    ) -> Dict[str, Any]:
        """Build the standard JSON-RPC payload for alchemy_getAssetTransfers."""
        if categories is None:
            categories = [TransferCategory.EXTERNAL.value, TransferCategory.ERC20.value]

        # maxCount must be hex or integer up to 1000
        clamped_count = max(1, min(max_count, 1000))
        max_count_hex = hex(clamped_count)

        params_dict: Dict[str, Any] = {
            "fromBlock": from_block,
            "toBlock": to_block,
            "category": categories,
            "withMetadata": True,
            "excludeZeroValue": False,
            "maxCount": max_count_hex,
        }

        if from_address:
            params_dict["fromAddress"] = from_address
        if to_address:
            params_dict["toAddress"] = to_address
        if page_key:
            params_dict["pageKey"] = page_key

        return {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "alchemy_getAssetTransfers",
            "params": [params_dict],
        }

    async def _execute_rpc_call(
        self,
        client: httpx.AsyncClient,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single JSON-RPC POST call to Alchemy and handle network/API errors."""
        if not self.settings.is_api_key_configured:
            raise AlchemyConfigError(
                "Alchemy API key is not configured or is using default placeholder in .env."
            )

        rpc_url = self.settings.alchemy_rpc_url

        try:
            response = await client.post(
                rpc_url,
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
        except httpx.TimeoutException:
            raise AlchemyNetworkError("Timeout communicating with Alchemy API.")
        except httpx.RequestError as exc:
            # Mask any accidental secrets from error messages
            raise AlchemyNetworkError(f"Network error connecting to Alchemy: {type(exc).__name__}")

        if response.status_code == 401 or response.status_code == 403:
            raise AlchemyAuthError("Alchemy rejected request: Invalid or unauthorized API key.")
        elif response.status_code == 429:
            raise AlchemyRateLimitError("Alchemy rate limit exceeded (HTTP 429).")
        elif response.status_code >= 500:
            raise AlchemyError(
                f"Alchemy server error (HTTP {response.status_code}).",
                status_code=502,
            )
        elif response.status_code != 200:
            raise AlchemyError(
                f"Unexpected HTTP {response.status_code} response from Alchemy.",
                status_code=502,
            )

        try:
            data = response.json()
        except Exception:
            raise AlchemyError("Received invalid non-JSON response from Alchemy.", status_code=502)

        # Check for JSON-RPC error payload
        if "error" in data:
            rpc_error = data["error"]
            err_code = rpc_error.get("code") if isinstance(rpc_error, dict) else "UNKNOWN"
            err_msg = rpc_error.get("message", "Unknown RPC error") if isinstance(rpc_error, dict) else str(rpc_error)
            
            # Detect auth errors embedded in RPC responses
            if "invalid api key" in err_msg.lower() or "unauthorized" in err_msg.lower() or err_code in (-32000, 401):
                raise AlchemyAuthError(f"Alchemy RPC Authentication Error: {err_msg}")
            
            raise AlchemyError(f"Alchemy RPC Error ({err_code}): {err_msg}", status_code=502)

        return data

    def parse_raw_transfer(self, raw: Dict[str, Any]) -> TransferItem:
        """
        Parse and normalize a single raw transfer item from Alchemy Transfers API.
        
        Explicitly handles differences between native ETH transfers (category='external')
        and smart contract token transfers (category='erc20', etc.).
        """
        # Block number conversion (from hex '0x...' or int)
        block_num_raw = raw.get("blockNum", "0x0")
        if isinstance(block_num_raw, str):
            try:
                block_number = int(block_num_raw, 16) if block_num_raw.startswith("0x") else int(block_num_raw)
            except ValueError:
                block_number = 0
        elif isinstance(block_num_raw, (int, float)):
            block_number = int(block_num_raw)
        else:
            block_number = 0

        category = raw.get("category", "unknown")
        asset = raw.get("asset")

        # Parse raw contract sub-object if present
        raw_contract_data = raw.get("rawContract") or {}
        raw_contract_obj = None
        contract_address = None

        if isinstance(raw_contract_data, dict) and raw_contract_data:
            contract_address = raw_contract_data.get("address")
            raw_contract_obj = RawContractInfo(
                address=contract_address,
                value=raw_contract_data.get("value"),
                decimal=raw_contract_data.get("decimal"),
            )

        # Distinguish ETH vs Token transfers
        if category in ("external", "internal"):
            # Native ETH transfer: contract_address is null, asset defaults to ETH
            if not asset:
                asset = "ETH"
            contract_address = None
        elif category == "erc20":
            # ERC-20 transfer: contract_address is the token contract
            if not contract_address and raw_contract_obj:
                contract_address = raw_contract_obj.address

        # Value parsing: normalized float amount provided by Alchemy
        raw_value = raw.get("value")
        parsed_value: Optional[float] = None
        if raw_value is not None:
            try:
                parsed_value = float(raw_value)
            except (ValueError, TypeError):
                parsed_value = None

        # Timestamp from metadata if withMetadata=True was supplied
        metadata = raw.get("metadata") or {}
        timestamp = metadata.get("blockTimestamp") if isinstance(metadata, dict) else None

        return TransferItem(
            transaction_hash=raw.get("hash", ""),
            from_address=(raw.get("from") or "").lower(),
            to_address=(raw.get("to") or "").lower() if raw.get("to") else None,
            asset=asset,
            value=parsed_value,
            block_number=block_number,
            category=category,
            contract_address=contract_address.lower() if contract_address else None,
            timestamp=timestamp,
            unique_id=raw.get("uniqueId"),
            raw_contract=raw_contract_obj,
        )

    async def get_wallet_transfers(
        self,
        address: str,
        direction: TransferDirection = TransferDirection.ALL,
        categories: Optional[List[str]] = None,
        max_count: int = 100,
        page_key: Optional[str] = None,
    ) -> TransferResponse:
        """
        Fetch and parse transfers for a given Ethereum address.

        Args:
            address: Validated, normalized Ethereum address.
            direction: 'all', 'from' (outgoing), or 'to' (incoming).
            categories: List of categories (defaults to ['external', 'erc20']).
            max_count: Maximum items to retrieve per request (max 1000).
            page_key: Pagination cursor key.

        Returns:
            TransferResponse containing list of normalized TransferItem objects.
        """
        client = await self._get_client()
        should_close_client = self._client is None

        network_name = "mainnet" if "mainnet" in self.settings.ALCHEMY_NETWORK else self.settings.ALCHEMY_NETWORK

        try:
            if direction == TransferDirection.FROM:
                payload = self._build_jsonrpc_payload(
                    from_address=address,
                    categories=categories,
                    max_count=max_count,
                    page_key=page_key,
                )
                rpc_response = await self._execute_rpc_call(client, payload)
                result = rpc_response.get("result", {})
                raw_transfers = result.get("transfers", [])
                next_page_key = result.get("pageKey")

                parsed_items = [self.parse_raw_transfer(t) for t in raw_transfers]
                return TransferResponse(
                    wallet_address=address,
                    blockchain="ethereum",
                    network=network_name,
                    direction=direction.value,
                    transfer_count=len(parsed_items),
                    page_key=next_page_key,
                    transfers=parsed_items,
                )

            elif direction == TransferDirection.TO:
                payload = self._build_jsonrpc_payload(
                    to_address=address,
                    categories=categories,
                    max_count=max_count,
                    page_key=page_key,
                )
                rpc_response = await self._execute_rpc_call(client, payload)
                result = rpc_response.get("result", {})
                raw_transfers = result.get("transfers", [])
                next_page_key = result.get("pageKey")

                parsed_items = [self.parse_raw_transfer(t) for t in raw_transfers]
                return TransferResponse(
                    wallet_address=address,
                    blockchain="ethereum",
                    network=network_name,
                    direction=direction.value,
                    transfer_count=len(parsed_items),
                    page_key=next_page_key,
                    transfers=parsed_items,
                )

            else:
                # Direction is 'ALL'
                if page_key:
                    payload = self._build_jsonrpc_payload(
                        from_address=address,
                        categories=categories,
                        max_count=max_count,
                        page_key=page_key,
                    )
                    rpc_response = await self._execute_rpc_call(client, payload)
                    result = rpc_response.get("result", {})
                    raw_transfers = result.get("transfers", [])
                    next_page_key = result.get("pageKey")
                    parsed_items = [self.parse_raw_transfer(t) for t in raw_transfers]
                    return TransferResponse(
                        wallet_address=address,
                        blockchain="ethereum",
                        network=network_name,
                        direction=direction.value,
                        transfer_count=len(parsed_items),
                        page_key=next_page_key,
                        transfers=parsed_items,
                    )

                # Query both outgoing and incoming concurrently
                payload_from = self._build_jsonrpc_payload(
                    from_address=address,
                    categories=categories,
                    max_count=max_count,
                )
                payload_to = self._build_jsonrpc_payload(
                    to_address=address,
                    categories=categories,
                    max_count=max_count,
                )

                resp_from, resp_to = await asyncio.gather(
                    self._execute_rpc_call(client, payload_from),
                    self._execute_rpc_call(client, payload_to),
                )

                transfers_from = resp_from.get("result", {}).get("transfers", [])
                transfers_to = resp_to.get("result", {}).get("transfers", [])

                # Parse and merge
                all_parsed: List[TransferItem] = []
                seen_unique_ids = set()

                for raw_t in transfers_from + transfers_to:
                    item = self.parse_raw_transfer(raw_t)
                    # Deduplicate in case of self-transfers (from == to)
                    dedup_key = item.unique_id or f"{item.transaction_hash}-{item.category}-{item.from_address}-{item.to_address}-{item.value}"
                    if dedup_key not in seen_unique_ids:
                        seen_unique_ids.add(dedup_key)
                        all_parsed.append(item)

                # Sort by block_number descending (newest transactions first)
                all_parsed.sort(key=lambda x: x.block_number, reverse=True)

                # Clamp to max_count
                clamped_items = all_parsed[:max_count]

                next_page_key = resp_from.get("result", {}).get("pageKey") or resp_to.get("result", {}).get("pageKey")

                return TransferResponse(
                    wallet_address=address,
                    blockchain="ethereum",
                    network=network_name,
                    direction=direction.value,
                    transfer_count=len(clamped_items),
                    page_key=next_page_key,
                    transfers=clamped_items,
                )

        finally:
            if should_close_client:
                await client.aclose()
