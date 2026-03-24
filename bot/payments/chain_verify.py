"""On-chain payment verification — base class and registry (Card 18)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class TxResult:
    found: bool
    tx_hash: Optional[str] = None
    amount: Optional[Decimal] = None       # Amount received in native units
    confirmations: Optional[int] = None
    from_address: Optional[str] = None
    block_height: Optional[int] = None
    timestamp: Optional[int] = None


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


# Import verifiers after definition to avoid circular imports
from bot.payments.verifiers.btc import BTCVerifier
from bot.payments.verifiers.ltc import LTCVerifier
from bot.payments.verifiers.sol import SOLVerifier
from bot.payments.verifiers.usdt_sol import USDTSolVerifier

VERIFIERS: dict[str, ChainVerifier] = {
    'btc': BTCVerifier(),
    'ltc': LTCVerifier(),
    'sol': SOLVerifier(),
    'usdt_sol': USDTSolVerifier(),
}


def get_verifier(coin: str) -> ChainVerifier:
    verifier = VERIFIERS.get(coin)
    if not verifier:
        raise ValueError(f"No verifier for coin: {coin}")
    return verifier
