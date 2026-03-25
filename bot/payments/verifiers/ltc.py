"""LTC on-chain verifier using BlockCypher API."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

import httpx

from bot.payments.chain_verify import ChainVerifier, TxResult

logger = logging.getLogger(__name__)

API_URL = "https://api.blockcypher.com/v1/ltc/main"

LITOSHI = Decimal("100000000")


class LTCVerifier(ChainVerifier):

    def required_confirmations(self) -> int:
        return 3

    def coin_name(self) -> str:
        return "LTC"

    async def check_payment(self, address: str, expected_amount: Decimal) -> TxResult:
        """Check if an LTC payment >= expected_amount was received at address."""
        try:
            return await self._query(address, expected_amount)
        except Exception:
            logger.error(
                "LTC verifier: failed to check address %s", address, exc_info=True
            )
            return TxResult(found=False)

    async def _query(self, address: str, expected_amount: Decimal) -> TxResult:
        params: dict[str, Any] = {"limit": 10}
        from bot.config.env import EnvKeys
        api_key = EnvKeys.BLOCKCYPHER_API_KEY
        if api_key:
            params["token"] = api_key

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{API_URL}/addrs/{address}", params=params)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()

        txrefs: list[dict[str, Any]] = data.get("txrefs", [])
        unconfirmed_txrefs: list[dict[str, Any]] = data.get(
            "unconfirmed_txrefs", []
        )

        # Check confirmed transactions first, then unconfirmed
        for txref in txrefs + unconfirmed_txrefs:
            # BlockCypher txrefs: positive value = received, tx_output_n >= 0
            value = txref.get("value", 0)
            if value <= 0:
                continue
            # Only consider outputs directed at this address (tx_output_n >= 0)
            if txref.get("tx_input_n", -1) >= 0:
                continue

            amount_ltc = Decimal(str(value)) / LITOSHI

            if amount_ltc >= expected_amount:
                confirmations = txref.get("confirmations", 0)
                return TxResult(
                    found=True,
                    tx_hash=txref.get("tx_hash"),
                    amount=amount_ltc,
                    confirmations=confirmations,
                    from_address=None,  # Not available in txrefs summary
                    block_height=txref.get("block_height"),
                    timestamp=None,
                )

        return TxResult(found=False)
