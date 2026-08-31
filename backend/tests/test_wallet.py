import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.alchemy import (
    AlchemyService,
    AlchemyAuthError,
    AlchemyRateLimitError,
    AlchemyConfigError,
)

VALID_ADDRESS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
NORM_ADDRESS = VALID_ADDRESS.lower()


@pytest.mark.asyncio
async def test_health_check():
    """Verify health check endpoint returns 200."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint():
    """Verify root endpoint returns project info."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "SIH" in data["project"]
    assert data["status"] == "online"


@pytest.mark.asyncio
async def test_invalid_ethereum_address_too_short():
    """Verify 400 response on invalid short address."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/wallet/0x12345/transfers")
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"] == "INVALID_ETHEREUM_ADDRESS"


@pytest.mark.asyncio
async def test_invalid_ethereum_address_bad_prefix():
    """Verify 400 response on address missing 0x prefix."""
    bad_addr = "d8dA6BF26964aF9D7eEd9e03E53415D37aA9604512"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/wallet/{bad_addr}/transfers")
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"] == "INVALID_ETHEREUM_ADDRESS"


@pytest.mark.asyncio
async def test_invalid_ethereum_address_non_hex():
    """Verify 400 response on address containing non-hex characters."""
    bad_addr = "0xZZdA6BF26964aF9D7eEd9e03E53415D37aA96045"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/wallet/{bad_addr}/transfers")
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"] == "INVALID_ETHEREUM_ADDRESS"


@pytest.mark.asyncio
async def test_valid_wallet_transfers_all(mock_alchemy_rpc_response):
    """Test retrieving transfers for valid wallet with mocked RPC response."""
    with patch.object(
        AlchemyService,
        "_execute_rpc_call",
        new=AsyncMock(return_value=mock_alchemy_rpc_response),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/wallet/{VALID_ADDRESS}/transfers")

        assert response.status_code == 200
        data = response.json()
        assert data["wallet_address"] == NORM_ADDRESS
        assert data["blockchain"] == "ethereum"
        assert data["network"] == "mainnet"
        assert data["direction"] == "all"
        assert data["transfer_count"] == 2
        assert len(data["transfers"]) == 2

        # Check native ETH item
        eth_item = next(t for t in data["transfers"] if t["category"] == "external")
        assert eth_item["asset"] == "ETH"
        assert eth_item["value"] == 1.25
        assert eth_item["contract_address"] is None
        assert eth_item["timestamp"] == "2024-03-15T14:30:00.000Z"

        # Check ERC-20 item
        erc20_item = next(t for t in data["transfers"] if t["category"] == "erc20")
        assert erc20_item["asset"] == "USDT"
        assert erc20_item["value"] == 5000.0
        assert erc20_item["contract_address"] == "0xdac17f958d2ee523a2206206994597c13d831ec7"


@pytest.mark.asyncio
async def test_valid_wallet_directional_from(mock_alchemy_rpc_response):
    """Test direction='from' returns directional response."""
    with patch.object(
        AlchemyService,
        "_execute_rpc_call",
        new=AsyncMock(return_value=mock_alchemy_rpc_response),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/wallet/{VALID_ADDRESS}/transfers?direction=from")

        assert response.status_code == 200
        data = response.json()
        assert data["direction"] == "from"
        assert data["transfer_count"] == 2
        assert data["page_key"] == "01234567-89ab-cdef-0123-456789abcdef"


@pytest.mark.asyncio
async def test_empty_wallet_transfers(mock_empty_rpc_response):
    """Test wallet with 0 transfer events returns empty list and 0 count."""
    with patch.object(
        AlchemyService,
        "_execute_rpc_call",
        new=AsyncMock(return_value=mock_empty_rpc_response),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/wallet/{VALID_ADDRESS}/transfers")

        assert response.status_code == 200
        data = response.json()
        assert data["wallet_address"] == NORM_ADDRESS
        assert data["blockchain"] == "ethereum"
        assert data["network"] == "mainnet"
        assert data["transfer_count"] == 0
        assert data["transfers"] == []


@pytest.mark.asyncio
async def test_alchemy_auth_error_handling():
    """Test handling when Alchemy returns authentication failure."""
    with patch.object(
        AlchemyService,
        "_execute_rpc_call",
        side_effect=AlchemyAuthError("Invalid API key provided."),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/wallet/{VALID_ADDRESS}/transfers")

        assert response.status_code == 502
        data = response.json()
        assert data["detail"]["error"] == "ALCHEMY_AUTH_ERROR"


@pytest.mark.asyncio
async def test_alchemy_rate_limit_handling():
    """Test handling when Alchemy returns 429 rate limit."""
    with patch.object(
        AlchemyService,
        "_execute_rpc_call",
        side_effect=AlchemyRateLimitError("Rate limit exceeded."),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/wallet/{VALID_ADDRESS}/transfers")

        assert response.status_code == 429
        data = response.json()
        assert data["detail"]["error"] == "RATE_LIMIT_EXCEEDED"
