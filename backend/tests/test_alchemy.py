import pytest
from app.services.alchemy import AlchemyService, AlchemyConfigError
from app.config import Settings


def test_parse_eth_transfer(mock_eth_transfer_raw):
    """Test parsing of native ETH (external) transfer."""
    service = AlchemyService()
    item = service.parse_raw_transfer(mock_eth_transfer_raw)

    assert item.transaction_hash == mock_eth_transfer_raw["hash"]
    assert item.from_address == mock_eth_transfer_raw["from"].lower()
    assert item.to_address == mock_eth_transfer_raw["to"].lower()
    assert item.asset == "ETH"
    assert item.value == 1.25
    assert item.category == "external"
    assert item.contract_address is None  # Native ETH has no contract address
    assert item.block_number == int("0x12a05f3", 16)
    assert item.timestamp == "2024-03-15T14:30:00.000Z"
    assert item.unique_id == mock_eth_transfer_raw["uniqueId"]


def test_parse_erc20_transfer(mock_erc20_transfer_raw):
    """Test parsing of ERC-20 token (USDT) transfer."""
    service = AlchemyService()
    item = service.parse_raw_transfer(mock_erc20_transfer_raw)

    assert item.transaction_hash == mock_erc20_transfer_raw["hash"]
    assert item.from_address == mock_erc20_transfer_raw["from"].lower()
    assert item.to_address == mock_erc20_transfer_raw["to"].lower()
    assert item.asset == "USDT"
    assert item.value == 5000.0
    assert item.category == "erc20"
    assert item.contract_address == "0xdac17f958d2ee523a2206206994597c13d831ec7"
    assert item.raw_contract is not None
    assert item.raw_contract.decimal == "0x6"
    assert item.block_number == int("0x12a0610", 16)
    assert item.timestamp == "2024-03-15T14:35:12.000Z"


def test_missing_api_key_raises_config_error():
    """Test that missing API key raises AlchemyConfigError."""
    settings = Settings(ALCHEMY_API_KEY="")
    service = AlchemyService(settings=settings)

    assert not settings.is_api_key_configured
