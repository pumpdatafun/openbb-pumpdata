"""Small helpers shared by the models."""

import re
from typing import Any

# a Solana address or mint: 32 to 44 base58 characters
BASE58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def check_address(value: str, what: str = "address") -> str:
    """Return the value stripped, or raise ValueError when it is not a Solana address."""
    v = (value or "").strip()
    if not BASE58.match(v):
        raise ValueError(f"{what}: not a Solana address (32 to 44 base58 characters): {value!r}")
    return v


def dig(obj: Any, *keys: str, default: Any = None) -> Any:
    """obj[k1][k2]..., or default when any step is missing."""
    for k in keys:
        if not isinstance(obj, dict) or k not in obj:
            return default
        obj = obj[k]
    return obj
