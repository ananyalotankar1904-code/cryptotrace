import re
from typing import Tuple


# Ethereum address regular expression: starts with '0x' followed by 40 hex digits (case-insensitive)
ETH_ADDRESS_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")


def is_valid_ethereum_address(address: str) -> bool:
    """
    Check if a string is a syntactically valid Ethereum address.

    Args:
        address: The Ethereum address string to validate.

    Returns:
        True if the address matches standard Ethereum 20-byte hex format, False otherwise.
    """
    if not isinstance(address, str):
        return False
    return bool(ETH_ADDRESS_REGEX.match(address.strip()))


def validate_ethereum_address(address: str) -> Tuple[bool, str]:
    """
    Validate an Ethereum address and return a standardized version or a specific error message.

    Args:
        address: The candidate Ethereum address string.

    Returns:
        A tuple of (is_valid, normalized_address_or_error_message).
    """
    if not address or not isinstance(address, str):
        return False, "Wallet address must be a non-empty string."

    trimmed = address.strip()

    if not trimmed.startswith("0x") and not trimmed.startswith("0X"):
        return False, "Invalid Ethereum address format: Address must start with '0x'."

    if len(trimmed) != 42:
        return (
            False,
            f"Invalid Ethereum address length: Expected 42 characters (including '0x'), got {len(trimmed)}.",
        )

    if not ETH_ADDRESS_REGEX.match(trimmed):
        return (
            False,
            "Invalid Ethereum address: Contains invalid non-hexadecimal characters.",
        )

    # Return normalized lowercase address
    return True, trimmed.lower()


def sanitize_ethereum_address(address: str) -> str:
    """
    Sanitize and lowercase an Ethereum address.

    Args:
        address: Valid Ethereum address.

    Returns:
        Lowercased 0x-prefixed address.
    """
    return address.strip().lower()
