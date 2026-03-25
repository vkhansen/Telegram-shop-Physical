"""BTC on-chain verifier using Blockstream.info API with mempool.space fallback."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

import httpx

from bot.payments.chain_verify import ChainVerifier, TxResult

logger = logging.getLogger(__name__)

API_URL = "https://blockstream.info/api"
FALLBACK_URL = "https://mempool.space/api"

SATOSHI = Decimal("100000000")


class BTCVerifier(ChainVerifier):

    def required_confirmations(self) -> int:
        return 2

    def coin_name(self) -> str:
        return "BTC"

    async def check_payment(self, address: str, expected_amount: Decimal) -> TxResult:
        """Check if a BTC payment >= expected_amount was received at address."""
        for base_url in (API_URL, FALLBACK_URL):
            try:
                return await self._check_with_api(base_url, address, expected_amount)
            except Exception:
                logger.warning(
                    "BTC verifier: %s failed for address %s, trying fallback",
                    base_url,
                    address,
                    exc_info=True,
                )
        logger.error("BTC verifier: all APIs failed for address %s", address)
        return TxResult(found=False)

    async def _check_with_api(
        self, base_url: str, address: str, expected_amount: Decimal
    ) -> TxResult:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Fetch transactions for the address
            txs_resp = await client.get(f"{base_url}/address/{address}/txs")
            txs_resp.raise_for_status()
            txs: list[dict[str, Any]] = txs_resp.json()

            if not txs:
                return TxResult(found=False)

            # Fetch current tip height for confirmation calculation
            tip_resp = await client.get(f"{base_url}/blocks/tip/height")
            tip_resp.raise_for_status()
            try:
                tip_height: int = int(tip_resp.text.strip())
            except (ValueError, AttributeError):
                logger.error("Invalid tip height response: %r", tip_resp.text)
                return TxResult(found=False)

            # Scan transactions for payments to our address
            for tx in txs:
                received = Decimal(0)
                for vout in tx.get("vout", []):
                    scriptpubkey_address = vout.get("scriptpubkey_address", "")
                    if scriptpubkey_address == address:
                        received += Decimal(str(vout.get("value", 0)))

                amount_btc = received / SATOSHI

                if amount_btc >= expected_amount:
                    tx_status = tx.get("status", {})
                    confirmed = tx_status.get("confirmed", False)
                    block_height = tx_status.get("block_height")
                    block_time = tx_status.get("block_time")

                    if confirmed and block_height is not None:
                        confirmations = tip_height - block_height + 1
                    else:
                        confirmations = 0

                    # Determine sender from first input
                    from_addr = None
                    vin_list = tx.get("vin", [])
                    if vin_list:
                        prevout = vin_list[0].get("prevout", {})
                        from_addr = prevout.get("scriptpubkey_address")

                    return TxResult(
                        found=True,
                        tx_hash=tx.get("txid"),
                        amount=amount_btc,
                        confirmations=confirmations,
                        from_address=from_addr,
                        block_height=block_height,
                        timestamp=block_time,
                    )

            return TxResult(found=False)
