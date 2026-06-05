"""On-chain payment verification — base class and registry (Card 18)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class TxResult:
    found: bool
    tx_hash: str | None = None
    amount: Decimal | None = None  # Amount received in native units
    confirmations: int | None = None
    from_address: str | None = None
    block_height: int | None = None
    timestamp: int | None = None


class ChainVerifier(ABC):
    """Base class for blockchain payment verifiers."""

    @abstractmethod
    async def check_payment(self, address: str, expected_amount: Decimal) -> TxResult:
        """Check if a payment >= expected_amount was received at address."""

    @abstractmethod
    def required_confirmations(self) -> int:
        """Minimum confirmations before payment is considered final."""

    @abstractmethod
    def coin_name(self) -> str:
        """Human-readable coin name for display."""


# Import verifiers after definition to avoid circular imports (they subclass
# ChainVerifier, which must be defined first) — E402 is intentional here.
from bot.payments.verifiers.btc import BTCVerifier  # noqa: E402
from bot.payments.verifiers.ltc import LTCVerifier  # noqa: E402
from bot.payments.verifiers.sol import SOLVerifier  # noqa: E402
from bot.payments.verifiers.usdt_sol import USDTSolVerifier  # noqa: E402

VERIFIERS: dict[str, ChainVerifier] = {
    "btc": BTCVerifier(),
    "ltc": LTCVerifier(),
    "sol": SOLVerifier(),
    "usdt_sol": USDTSolVerifier(),
}


def get_verifier(coin: str) -> ChainVerifier:
    verifier = VERIFIERS.get(coin)
    if not verifier:
        raise ValueError(f"No verifier for coin: {coin}")
    return verifier
