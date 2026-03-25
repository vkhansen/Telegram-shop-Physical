"""SOL on-chain verifier using Solana JSON-RPC."""

from __future__ import annotations

import logging
import os
from decimal import Decimal
from typing import Any, Optional

import httpx

from bot.payments.chain_verify import ChainVerifier, TxResult

logger = logging.getLogger(__name__)

DEFAULT_RPC_URL = "https://api.mainnet-beta.solana.com"

LAMPORTS = Decimal("1000000000")


class SOLVerifier(ChainVerifier):

    def required_confirmations(self) -> int:
        return 1  # finalized commitment already implies sufficient confirmations

    def coin_name(self) -> str:
        return "SOL"

    @staticmethod
    def _rpc_url() -> str:
        from bot.config.env import EnvKeys
        return EnvKeys.SOLANA_RPC_URL

    async def check_payment(self, address: str, expected_amount: Decimal) -> TxResult:
        """Check if a SOL payment >= expected_amount was received at address."""
        try:
            return await self._query(address, expected_amount)
        except Exception:
            logger.error(
                "SOL verifier: failed to check address %s", address, exc_info=True
            )
            return TxResult(found=False)

    async def _query(self, address: str, expected_amount: Decimal) -> TxResult:
        rpc_url = self._rpc_url()

        async with httpx.AsyncClient(timeout=20.0) as client:
            # Step 1: get recent signatures for the address
            sigs_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [
                    address,
                    {"limit": 10, "commitment": "finalized"},
                ],
            }
            sigs_resp = await client.post(rpc_url, json=sigs_payload)
            sigs_resp.raise_for_status()
            sigs_data = sigs_resp.json()

            signatures: list[dict[str, Any]] = sigs_data.get("result", [])
            if not signatures:
                return TxResult(found=False)

            # Step 2: inspect each transaction
            for sig_info in signatures:
                signature = sig_info.get("signature")
                if not signature:
                    continue
                # Skip errored transactions
                if sig_info.get("err") is not None:
                    continue

                tx_result = await self._check_transaction(
                    client, rpc_url, signature, address, expected_amount
                )
                if tx_result and tx_result.found:
                    return tx_result

        return TxResult(found=False)

    async def _check_transaction(
        self,
        client: httpx.AsyncClient,
        rpc_url: str,
        signature: str,
        address: str,
        expected_amount: Decimal,
    ) -> Optional[TxResult]:
        tx_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                signature,
                {"encoding": "jsonParsed", "commitment": "finalized"},
            ],
        }
        tx_resp = await client.post(rpc_url, json=tx_payload)
        tx_resp.raise_for_status()
        tx_data = tx_resp.json()

        result = tx_data.get("result")
        if not result:
            return None

        meta = result.get("meta")
        if not meta or meta.get("err") is not None:
            return None

        transaction = result.get("transaction", {})
        message = transaction.get("message", {})
        account_keys = message.get("accountKeys", [])

        # Build list of account pubkeys
        accounts: list[str] = []
        for key_entry in account_keys:
            if isinstance(key_entry, dict):
                accounts.append(key_entry.get("pubkey", ""))
            else:
                accounts.append(str(key_entry))

        # Find the index of our address
        try:
            addr_index = accounts.index(address)
        except ValueError:
            return None

        pre_balances: list[int] = meta.get("preBalances", [])
        post_balances: list[int] = meta.get("postBalances", [])

        if addr_index >= len(pre_balances) or addr_index >= len(post_balances):
            return None

        pre = pre_balances[addr_index]
        post = post_balances[addr_index]
        diff = post - pre

        if diff <= 0:
            return None

        amount_sol = Decimal(str(diff)) / LAMPORTS

        if amount_sol >= expected_amount:
            # Determine sender: first account that lost SOL
            from_address = None
            for i, acct in enumerate(accounts):
                if i == addr_index:
                    continue
                if i < len(pre_balances) and i < len(post_balances):
                    if post_balances[i] < pre_balances[i]:
                        from_address = acct
                        break

            slot = result.get("slot")
            block_time = result.get("blockTime")

            return TxResult(
                found=True,
                tx_hash=signature,
                amount=amount_sol,
                confirmations=1,  # finalized
                from_address=from_address,
                block_height=slot,
                timestamp=block_time,
            )

        return None
