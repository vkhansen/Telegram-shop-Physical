"""USDT on Solana (SPL token) on-chain verifier using Solana JSON-RPC."""

from __future__ import annotations

import logging
import os
from decimal import Decimal
from typing import Any, Optional

import httpx

from bot.payments.chain_verify import ChainVerifier, TxResult

logger = logging.getLogger(__name__)

DEFAULT_RPC_URL = "https://api.mainnet-beta.solana.com"

# USDT SPL token mint on Solana mainnet
USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"

# USDT has 6 decimals on Solana
USDT_DECIMALS = Decimal("1000000")


class USDTSolVerifier(ChainVerifier):

    def required_confirmations(self) -> int:
        return 1  # finalized commitment

    def coin_name(self) -> str:
        return "USDT (SOL)"

    @staticmethod
    def _rpc_url() -> str:
        return os.environ.get("SOLANA_RPC_URL", DEFAULT_RPC_URL)

    async def check_payment(self, address: str, expected_amount: Decimal) -> TxResult:
        """Check if a USDT payment >= expected_amount was received at address."""
        try:
            return await self._query(address, expected_amount)
        except Exception:
            logger.error(
                "USDT-SOL verifier: failed to check address %s",
                address,
                exc_info=True,
            )
            return TxResult(found=False)

    async def _query(self, address: str, expected_amount: Decimal) -> TxResult:
        rpc_url = self._rpc_url()

        async with httpx.AsyncClient(timeout=20.0) as client:
            # Step 1: find the associated token account for USDT
            token_accounts = await self._get_token_accounts(client, rpc_url, address)
            if not token_accounts:
                return TxResult(found=False)

            # Step 2: get recent signatures for each token account
            for token_account in token_accounts:
                result = await self._check_token_account(
                    client, rpc_url, token_account, address, expected_amount
                )
                if result and result.found:
                    return result

        return TxResult(found=False)

    async def _get_token_accounts(
        self, client: httpx.AsyncClient, rpc_url: str, owner: str
    ) -> list[str]:
        """Get all USDT token accounts owned by the given address."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                owner,
                {"mint": USDT_MINT},
                {"encoding": "jsonParsed"},
            ],
        }
        resp = await client.post(rpc_url, json=payload)
        resp.raise_for_status()
        data = resp.json()

        result = data.get("result", {})
        accounts: list[str] = []
        for item in result.get("value", []):
            pubkey = item.get("pubkey")
            if pubkey:
                accounts.append(pubkey)

        return accounts

    async def _check_token_account(
        self,
        client: httpx.AsyncClient,
        rpc_url: str,
        token_account: str,
        owner_address: str,
        expected_amount: Decimal,
    ) -> Optional[TxResult]:
        """Check recent transactions on a token account for incoming USDT."""
        # Get recent signatures for the token account
        sigs_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [
                token_account,
                {"limit": 10, "commitment": "finalized"},
            ],
        }
        sigs_resp = await client.post(rpc_url, json=sigs_payload)
        sigs_resp.raise_for_status()
        sigs_data = sigs_resp.json()

        signatures: list[dict[str, Any]] = sigs_data.get("result", [])

        for sig_info in signatures:
            signature = sig_info.get("signature")
            if not signature:
                continue
            if sig_info.get("err") is not None:
                continue

            result = await self._check_transaction(
                client, rpc_url, signature, token_account, owner_address, expected_amount
            )
            if result and result.found:
                return result

        return None

    async def _check_transaction(
        self,
        client: httpx.AsyncClient,
        rpc_url: str,
        signature: str,
        token_account: str,
        owner_address: str,
        expected_amount: Decimal,
    ) -> Optional[TxResult]:
        """Inspect a single transaction for USDT received."""
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

        pre_token_balances: list[dict[str, Any]] = meta.get("preTokenBalances", [])
        post_token_balances: list[dict[str, Any]] = meta.get("postTokenBalances", [])

        # Build mapping: accountIndex -> pre/post uiTokenAmount for our USDT mint
        pre_amounts: dict[int, Decimal] = {}
        post_amounts: dict[int, Decimal] = {}

        for bal in pre_token_balances:
            if bal.get("mint") == USDT_MINT and bal.get("owner") == owner_address:
                idx = bal.get("accountIndex", -1)
                ui_amount = bal.get("uiTokenAmount", {})
                amount_str = ui_amount.get("amount", "0")
                pre_amounts[idx] = Decimal(amount_str)

        for bal in post_token_balances:
            if bal.get("mint") == USDT_MINT and bal.get("owner") == owner_address:
                idx = bal.get("accountIndex", -1)
                ui_amount = bal.get("uiTokenAmount", {})
                amount_str = ui_amount.get("amount", "0")
                post_amounts[idx] = Decimal(amount_str)

        # Compute the increase across all relevant account indices
        all_indices = set(pre_amounts.keys()) | set(post_amounts.keys())

        for idx in all_indices:
            pre_val = pre_amounts.get(idx, Decimal(0))
            post_val = post_amounts.get(idx, Decimal(0))
            diff = post_val - pre_val

            if diff <= 0:
                continue

            amount_usdt = diff / USDT_DECIMALS

            if amount_usdt >= expected_amount:
                # Try to determine sender from preTokenBalances
                from_address = None
                for bal in pre_token_balances:
                    if bal.get("mint") == USDT_MINT and bal.get("owner") != owner_address:
                        # Check if this owner's balance decreased
                        sender_owner = bal.get("owner")
                        sender_idx = bal.get("accountIndex", -1)
                        sender_pre = Decimal(
                            bal.get("uiTokenAmount", {}).get("amount", "0")
                        )
                        # Find matching post balance
                        for post_bal in post_token_balances:
                            if (
                                post_bal.get("accountIndex") == sender_idx
                                and post_bal.get("mint") == USDT_MINT
                            ):
                                sender_post = Decimal(
                                    post_bal.get("uiTokenAmount", {}).get("amount", "0")
                                )
                                if sender_post < sender_pre:
                                    from_address = sender_owner
                                    break
                        if from_address:
                            break

                slot = result.get("slot")
                block_time = result.get("blockTime")

                return TxResult(
                    found=True,
                    tx_hash=signature,
                    amount=amount_usdt,
                    confirmations=1,  # finalized
                    from_address=from_address,
                    block_height=slot,
                    timestamp=block_time,
                )

        return None
