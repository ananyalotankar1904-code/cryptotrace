import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import Settings
from app.models.transfer import TransferResponse, TransferItem
from app.services.alchemy import AlchemyService, AlchemyAuthError, AlchemyRateLimitError
from app.services.tracer import MultiHopTracer

ADDR_A = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
ADDR_B = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
ADDR_C = "0xcccccccccccccccccccccccccccccccccccccccc"
ADDR_D = "0xdddddddddddddddddddddddddddddddddddddddd"
BURN_ADDR = "0x0000000000000000000000000000000000000000"


def make_transfer(from_addr: str, to_addr: str, asset: str = "ETH", value: float = 1.0, category: str = "external", tx_hash: str = "0x123", block: int = 100, contract_addr: str = None) -> TransferItem:
    return TransferItem(
        transaction_hash=tx_hash,
        from_address=from_addr.lower(),
        to_address=to_addr.lower() if to_addr else None,
        asset=asset,
        value=value,
        block_number=block,
        category=category,
        contract_address=contract_addr.lower() if contract_addr else None,
        timestamp="2024-01-01T00:00:00Z",
        unique_id=f"{tx_hash}:{category}:{from_addr}:{to_addr}:{value}",
    )


@pytest.mark.asyncio
async def test_tracer_single_hop():
    """Test max_depth=1 only queries root wallet outgoing transfers."""
    mock_service = AsyncMock(spec=AlchemyService)
    mock_service.get_wallet_transfers.return_value = TransferResponse(
        wallet_address=ADDR_A,
        blockchain="ethereum",
        network="mainnet",
        direction="from",
        transfer_count=2,
        page_key=None,
        transfers=[
            make_transfer(ADDR_A, ADDR_B, asset="ETH", value=2.5, tx_hash="0xa_b_1"),
            make_transfer(ADDR_A, ADDR_C, asset="USDT", value=500.0, category="erc20", contract_addr="0xdac17f958d2ee523a2206206994597c13d831ec7", tx_hash="0xa_c_1"),
        ],
    )

    tracer = MultiHopTracer(alchemy_service=mock_service)
    result = await tracer.trace_wallet(root_address=ADDR_A, max_depth=1)

    assert result.root_wallet == ADDR_A
    assert result.max_depth == 1
    assert result.summary.max_hop_reached == 1
    assert result.summary.wallets_queried == 1
    assert result.summary.total_paths == 2
    assert len(result.paths) == 2
    assert result.summary.unique_addresses_discovered == 3  # A, B, C

    # Verify mock was only called once for root wallet A
    assert mock_service.get_wallet_transfers.call_count == 1
    call_args = mock_service.get_wallet_transfers.call_args_list[0]
    assert call_args.kwargs["address"] == ADDR_A


@pytest.mark.asyncio
async def test_tracer_multi_hop_bfs():
    """Test BFS traces A -> B -> D (2 hops) with proper hop numbering."""
    async def mock_get_transfers(address, direction, categories, max_count):
        if address == ADDR_A:
            return TransferResponse(
                wallet_address=ADDR_A,
                blockchain="ethereum",
                network="mainnet",
                direction="from",
                transfer_count=1,
                transfers=[make_transfer(ADDR_A, ADDR_B, value=1.0, tx_hash="0x1")],
            )
        elif address == ADDR_B:
            return TransferResponse(
                wallet_address=ADDR_B,
                blockchain="ethereum",
                network="mainnet",
                direction="from",
                transfer_count=1,
                transfers=[make_transfer(ADDR_B, ADDR_D, value=0.9, tx_hash="0x2")],
            )
        return TransferResponse(
            wallet_address=address,
            blockchain="ethereum",
            network="mainnet",
            direction="from",
            transfer_count=0,
            transfers=[],
        )

    mock_service = AsyncMock(spec=AlchemyService)
    mock_service.get_wallet_transfers.side_effect = mock_get_transfers

    tracer = MultiHopTracer(alchemy_service=mock_service)
    result = await tracer.trace_wallet(root_address=ADDR_A, max_depth=2)

    assert result.summary.max_hop_reached == 2
    assert result.summary.wallets_queried == 2
    assert len(result.paths) == 2
    assert result.paths[0].hop == 1
    assert result.paths[0].from_address == ADDR_A
    assert result.paths[0].to_address == ADDR_B
    assert result.paths[1].hop == 2
    assert result.paths[1].from_address == ADDR_B
    assert result.paths[1].to_address == ADDR_D


@pytest.mark.asyncio
async def test_tracer_loop_prevention():
    """
    Test cycle prevention: A -> B -> A.
    Edge B -> A is recorded at hop 2, but A is NOT queried again as hop 3.
    """
    async def mock_get_transfers(address, direction, categories, max_count):
        if address == ADDR_A:
            return TransferResponse(
                wallet_address=ADDR_A,
                blockchain="ethereum",
                network="mainnet",
                direction="from",
                transfer_count=1,
                transfers=[make_transfer(ADDR_A, ADDR_B, value=1.0, tx_hash="0xab")],
            )
        elif address == ADDR_B:
            # B sends back to A (cycle!)
            return TransferResponse(
                wallet_address=ADDR_B,
                blockchain="ethereum",
                network="mainnet",
                direction="from",
                transfer_count=1,
                transfers=[make_transfer(ADDR_B, ADDR_A, value=0.5, tx_hash="0xba")],
            )
        return TransferResponse(
            wallet_address=address,
            blockchain="ethereum",
            network="mainnet",
            direction="from",
            transfer_count=0,
            transfers=[],
        )

    mock_service = AsyncMock(spec=AlchemyService)
    mock_service.get_wallet_transfers.side_effect = mock_get_transfers

    tracer = MultiHopTracer(alchemy_service=mock_service)
    result = await tracer.trace_wallet(root_address=ADDR_A, max_depth=4)

    # A should NOT be queried a second time
    assert mock_service.get_wallet_transfers.call_count == 2
    queried_addresses = [call.kwargs["address"] for call in mock_service.get_wallet_transfers.call_args_list]
    assert queried_addresses == [ADDR_A, ADDR_B]

    # Paths should contain A -> B (hop 1) and B -> A (hop 2)
    assert len(result.paths) == 2
    assert result.paths[0].hop == 1
    assert result.paths[0].from_address == ADDR_A
    assert result.paths[0].to_address == ADDR_B
    assert result.paths[1].hop == 2
    assert result.paths[1].from_address == ADDR_B
    assert result.paths[1].to_address == ADDR_A


@pytest.mark.asyncio
async def test_tracer_terminal_burn_address():
    """Test that burn addresses (0x0...0) are recorded as paths but not queried for outgoing transfers."""
    async def mock_get_transfers(address, direction, categories, max_count):
        if address == ADDR_A:
            return TransferResponse(
                wallet_address=ADDR_A,
                blockchain="ethereum",
                network="mainnet",
                direction="from",
                transfer_count=1,
                transfers=[make_transfer(ADDR_A, BURN_ADDR, value=1.0, tx_hash="0xburn")],
            )
        return TransferResponse(
            wallet_address=address,
            blockchain="ethereum",
            network="mainnet",
            direction="from",
            transfer_count=0,
            transfers=[],
        )

    mock_service = AsyncMock(spec=AlchemyService)
    mock_service.get_wallet_transfers.side_effect = mock_get_transfers

    tracer = MultiHopTracer(alchemy_service=mock_service)
    result = await tracer.trace_wallet(root_address=ADDR_A, max_depth=3)

    assert len(result.paths) == 1
    assert result.paths[0].to_address == BURN_ADDR
    assert result.paths[0].is_contract_destination is True
    # Only root address A was queried; BURN_ADDR was not enqueued
    assert mock_service.get_wallet_transfers.call_count == 1


@pytest.mark.asyncio
async def test_tracer_empty_wallet():
    """Test wallet with no outgoing transfers returns 0 paths and 0 max hop."""
    mock_service = AsyncMock(spec=AlchemyService)
    mock_service.get_wallet_transfers.return_value = TransferResponse(
        wallet_address=ADDR_A,
        blockchain="ethereum",
        network="mainnet",
        direction="from",
        transfer_count=0,
        transfers=[],
    )

    tracer = MultiHopTracer(alchemy_service=mock_service)
    result = await tracer.trace_wallet(root_address=ADDR_A, max_depth=3)

    assert result.summary.transfers_analyzed == 0
    assert result.summary.total_paths == 0
    assert result.summary.max_hop_reached == 0
    assert result.summary.unique_addresses_discovered == 1
    assert result.paths == []


@pytest.mark.asyncio
async def test_tracer_pagination_warning():
    """Test that pagination on a node sets pagination_occurred=True and adds a warning."""
    mock_service = AsyncMock(spec=AlchemyService)
    mock_service.get_wallet_transfers.return_value = TransferResponse(
        wallet_address=ADDR_A,
        blockchain="ethereum",
        network="mainnet",
        direction="from",
        transfer_count=1,
        page_key="cursor_token_123",
        transfers=[make_transfer(ADDR_A, ADDR_B, value=1.0, tx_hash="0xpage")],
    )

    tracer = MultiHopTracer(alchemy_service=mock_service)
    result = await tracer.trace_wallet(root_address=ADDR_A, max_depth=1)

    assert result.summary.pagination_occurred is True
    assert any("additional outgoing transfers" in w for w in result.summary.warnings)


@pytest.mark.asyncio
async def test_trace_endpoint_valid_request():
    """Test GET /wallet/{address}/trace returns 200 with serialized from/to aliases."""
    mock_response = TransferResponse(
        wallet_address=ADDR_A,
        blockchain="ethereum",
        network="mainnet",
        direction="from",
        transfer_count=1,
        transfers=[make_transfer(ADDR_A, ADDR_B, asset="ETH", value=1.5, tx_hash="0xtx1")],
    )

    with patch.object(AlchemyService, "get_wallet_transfers", new=AsyncMock(return_value=mock_response)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/wallet/{ADDR_A}/trace?max_depth=1")

        assert response.status_code == 200
        data = response.json()
        assert data["root_wallet"] == ADDR_A
        assert data["blockchain"] == "ethereum"
        assert data["max_depth"] == 1
        assert "summary" in data
        assert data["summary"]["unique_addresses_discovered"] == 2
        assert len(data["paths"]) == 1
        
        # Verify JSON alias serialization: "from" and "to"
        path = data["paths"][0]
        assert path["from"] == ADDR_A
        assert path["to"] == ADDR_B
        assert path["asset"] == "ETH"
        assert path["value"] == 1.5
        assert path["hop"] == 1


@pytest.mark.asyncio
async def test_trace_endpoint_invalid_address():
    """Test GET /wallet/{address}/trace with invalid address returns 400."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/wallet/invalid_address_123/trace")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"] == "INVALID_ETHEREUM_ADDRESS"


@pytest.mark.asyncio
async def test_trace_endpoint_depth_clamping():
    """Test that max_depth > 5 is rejected or clamped by FastAPI validation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/wallet/{ADDR_A}/trace?max_depth=10")

    # FastAPI validation should catch max_depth > 5 and return 422
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_trace_diamond_graph():
    """
    Test diamond graph:
    A -> B (hop 1), A -> C (hop 1)
    B -> D (hop 2), C -> D (hop 2)
    D should be queued only once despite two parents.
    """
    async def mock_get_transfers(address, direction, categories, max_count):
        if address == ADDR_A:
            return TransferResponse(
                wallet_address=ADDR_A,
                blockchain="ethereum",
                network="mainnet",
                direction="from",
                transfer_count=2,
                transfers=[
                    make_transfer(ADDR_A, ADDR_B, value=1.0, tx_hash="0xab"),
                    make_transfer(ADDR_A, ADDR_C, value=2.0, tx_hash="0xac"),
                ],
            )
        elif address == ADDR_B:
            return TransferResponse(
                wallet_address=ADDR_B,
                blockchain="ethereum",
                network="mainnet",
                direction="from",
                transfer_count=1,
                transfers=[make_transfer(ADDR_B, ADDR_D, value=0.5, tx_hash="0xbd")],
            )
        elif address == ADDR_C:
            return TransferResponse(
                wallet_address=ADDR_C,
                blockchain="ethereum",
                network="mainnet",
                direction="from",
                transfer_count=1,
                transfers=[make_transfer(ADDR_C, ADDR_D, value=1.5, tx_hash="0xcd")],
            )
        elif address == ADDR_D:
            return TransferResponse(
                wallet_address=ADDR_D,
                blockchain="ethereum",
                network="mainnet",
                direction="from",
                transfer_count=0,
                transfers=[],
            )
        return TransferResponse(wallet_address=address, blockchain="ethereum", network="mainnet", direction="from", transfer_count=0, transfers=[])

    mock_service = AsyncMock(spec=AlchemyService)
    mock_service.get_wallet_transfers.side_effect = mock_get_transfers

    tracer = MultiHopTracer(alchemy_service=mock_service)
    result = await tracer.trace_wallet(root_address=ADDR_A, max_depth=3)

    assert result.summary.total_paths == 4  # A->B, A->C, B->D, C->D
    assert result.summary.unique_addresses_discovered == 4  # A, B, C, D
    # ADDR_D was queued only once
    queried = [call.kwargs["address"] for call in mock_service.get_wallet_transfers.call_args_list]
    assert queried.count(ADDR_D) == 1


@pytest.mark.asyncio
async def test_trace_endpoint_auth_error():
    """Test that AlchemyAuthError propagates as 502 with structured error response."""
    with patch.object(AlchemyService, "get_wallet_transfers", side_effect=AlchemyAuthError("Invalid key")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/wallet/{ADDR_A}/trace")

        assert response.status_code == 502
        data = response.json()
        assert data["detail"]["error"] == "ALCHEMY_AUTH_ERROR"


@pytest.mark.asyncio
async def test_trace_endpoint_rate_limit_error():
    """Test that AlchemyRateLimitError propagates as 429 with structured error response."""
    with patch.object(AlchemyService, "get_wallet_transfers", side_effect=AlchemyRateLimitError("Rate limit")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/wallet/{ADDR_A}/trace")

        assert response.status_code == 429
        data = response.json()
        assert data["detail"]["error"] == "RATE_LIMIT_EXCEEDED"

