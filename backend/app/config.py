import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    ALCHEMY_API_KEY: str = ""
    ALCHEMY_NETWORK: str = "eth-mainnet"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = False
    REQUEST_TIMEOUT_SECONDS: float = 15.0
    DEFAULT_MAX_DEPTH: int = 3
    MAX_DEPTH_LIMIT: int = 5
    DEFAULT_MAX_TRANSFERS_PER_WALLET: int = 25
    MAX_TRANSFERS_PER_WALLET_LIMIT: int = 100
    MAX_TOTAL_WALLETS_TRACED: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def alchemy_rpc_url(self) -> str:
        """Construct the Alchemy JSON-RPC endpoint URL."""
        key = self.ALCHEMY_API_KEY.strip()
        return f"https://{self.ALCHEMY_NETWORK}.g.alchemy.com/v2/{key}"

    @property
    def is_api_key_configured(self) -> bool:
        """Check if a valid, non-placeholder API key is configured."""
        key = self.ALCHEMY_API_KEY.strip()
        placeholder_values = {
            "",
            "your_alchemy_api_key_here",
            "your_api_key_here",
            "placeholder",
        }
        return key not in placeholder_values


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    return Settings()
