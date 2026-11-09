"""Minimal, secret-safe Supabase REST persistence for Fortunis8.

The service-role secret is sent only in the `apikey` header. Response bodies,
request headers, and credentials are never logged or attached to exceptions.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

import httpx

from app.services.domain import supported_personas

Language = Literal["en", "ur"]
SUPPORTED_LANGUAGES = frozenset({"en", "ur"})
USERS_TABLE = "fortunis8_users"
ACCOUNTS_TABLE = "fortunis8_accounts"


class PersistenceError(RuntimeError):
    """A storage failure that intentionally omits provider response details."""


class SupabaseRestUserStore:
    """Data access for the bot's namespaced, additive Fortunis8 tables."""

    def __init__(
        self,
        supabase_url: str,
        secret_key: str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._secret_key = secret_key
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=f"{supabase_url.rstrip('/')}/rest/v1/",
            timeout=httpx.Timeout(12.0, connect=5.0),
        )

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        prefer: str | None = None,
    ) -> httpx.Response:
        headers = {"apikey": self._secret_key, "Accept": "application/json"}
        if json is not None:
            headers["Content-Type"] = "application/json"
        if prefer:
            headers["Prefer"] = prefer
        try:
            response = await self._client.request(
                method, path, params=params, json=json, headers=headers
            )
        except httpx.HTTPError:
            raise PersistenceError("Supabase request failed.") from None
        if not 200 <= response.status_code < 300:
            raise PersistenceError(f"Supabase returned HTTP {response.status_code}.")
        return response

    @staticmethod
    def _validate_user_id(telegram_user_id: int) -> None:
        if (
            isinstance(telegram_user_id, bool)
            or not isinstance(telegram_user_id, int)
            or telegram_user_id <= 0
        ):
            raise ValueError("telegram_user_id must be a positive integer.")

    @staticmethod
    def _decode_json(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            raise PersistenceError("Supabase returned an invalid response.") from None

    async def _rpc(self, name: str, payload: dict[str, Any]) -> Any:
        response = await self._request("POST", f"rpc/{name}", json=payload)
        return self._decode_json(response)

    async def _read_language(self, telegram_user_id: int) -> Language | None:
        response = await self._request(
            "GET",
            USERS_TABLE,
            params={"select": "language", "telegram_user_id": f"eq.{telegram_user_id}", "limit": "1"},
        )
        rows = self._decode_json(response)
        if not isinstance(rows, list):
            raise PersistenceError("Supabase returned an invalid user record.")
        if not rows:
            return None
        if not isinstance(rows[0], dict):
            raise PersistenceError("Supabase returned an invalid user record.")
        language = rows[0].get("language")
        if language not in SUPPORTED_LANGUAGES:
            raise PersistenceError("Stored language is not supported.")
        return language  # type: ignore[return-value]

    async def get_or_create_language(self, telegram_user_id: int) -> Language:
        self._validate_user_id(telegram_user_id)
        language = await self._read_language(telegram_user_id)
        if language is not None:
            return language
        await self._request(
            "POST",
            USERS_TABLE,
            params={"on_conflict": "telegram_user_id"},
            json={"telegram_user_id": telegram_user_id},
            prefer="resolution=ignore-duplicates,return=minimal",
        )
        language = await self._read_language(telegram_user_id)
        if language is None:
            raise PersistenceError("User row was not available after insert.")
        return language

    async def set_language(self, telegram_user_id: int, language: str) -> Language:
        self._validate_user_id(telegram_user_id)
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError("language must be 'en' or 'ur'.")
        response = await self._request(
            "PATCH",
            USERS_TABLE,
            params={"select": "language", "telegram_user_id": f"eq.{telegram_user_id}"},
            json={"language": language},
            prefer="return=representation",
        )
        rows = self._decode_json(response)
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            raise PersistenceError("User language was not updated.")
        saved = rows[0].get("language")
        if saved not in SUPPORTED_LANGUAGES:
            raise PersistenceError("Supabase returned an invalid language.")
        return saved  # type: ignore[return-value]

    async def ensure_account(self, telegram_user_id: int) -> None:
        self._validate_user_id(telegram_user_id)
        await self.get_or_create_language(telegram_user_id)
        await self._request(
            "POST",
            ACCOUNTS_TABLE,
            params={"on_conflict": "telegram_user_id"},
            json={"telegram_user_id": telegram_user_id},
            prefer="resolution=ignore-duplicates,return=minimal",
        )

    async def get_account(self, telegram_user_id: int) -> dict[str, Any]:
        self._validate_user_id(telegram_user_id)
        await self.ensure_account(telegram_user_id)
        response = await self._request(
            "GET",
            ACCOUNTS_TABLE,
            params={
                "select": "diamonds,level,streak_count,selected_persona,premium_reading_credits",
                "telegram_user_id": f"eq.{telegram_user_id}",
                "limit": "1",
            },
        )
        rows = self._decode_json(response)
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            raise PersistenceError("Fortunis8 account is unavailable.")
        return rows[0]

    async def set_persona(self, telegram_user_id: int, persona: str) -> None:
        self._validate_user_id(telegram_user_id)
        if persona not in supported_personas():
            raise ValueError("Unsupported persona.")
        await self.ensure_account(telegram_user_id)
        response = await self._request(
            "PATCH",
            ACCOUNTS_TABLE,
            params={"telegram_user_id": f"eq.{telegram_user_id}"},
            json={"selected_persona": persona},
            prefer="return=minimal",
        )
        if response.status_code == 204:
            return
        # A successful PATCH may return an empty body depending on PostgREST.
        if response.content not in (b"", b"[]"):
            self._decode_json(response)

    async def save_reading(
        self,
        telegram_user_id: int,
        reading_type: str,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._validate_user_id(telegram_user_id)
        await self.ensure_account(telegram_user_id)
        await self._request(
            "POST",
            "fortunis8_readings",
            json={
                "telegram_user_id": telegram_user_id,
                "reading_type": reading_type,
                "title": title[:120],
                "content": content[:3500],
                "metadata": metadata or {},
            },
            prefer="return=minimal",
        )

    async def get_last_reading(self, telegram_user_id: int) -> dict[str, Any] | None:
        self._validate_user_id(telegram_user_id)
        response = await self._request(
            "GET",
            "fortunis8_readings",
            params={
                "select": "reading_type,title,content,created_at",
                "telegram_user_id": f"eq.{telegram_user_id}",
                "order": "created_at.desc",
                "limit": "1",
            },
        )
        rows = self._decode_json(response)
        if not isinstance(rows, list) or (rows and not isinstance(rows[0], dict)):
            raise PersistenceError("Supabase returned an invalid reading record.")
        return rows[0] if rows else None

    async def claim_daily(self, telegram_user_id: int) -> dict[str, Any]:
        self._validate_user_id(telegram_user_id)
        result = await self._rpc(
            "fortunis8_claim_daily", {"p_telegram_user_id": telegram_user_id}
        )
        if not isinstance(result, dict):
            raise PersistenceError("Daily reward result was invalid.")
        return result

    async def claim_charity_quest(
        self, telegram_user_id: int, quest_key: str
    ) -> dict[str, Any]:
        self._validate_user_id(telegram_user_id)
        result = await self._rpc(
            "fortunis8_claim_charity_quest",
            {"p_telegram_user_id": telegram_user_id, "p_quest_key": quest_key},
        )
        if not isinstance(result, dict):
            raise PersistenceError("Quest result was invalid.")
        return result

    async def create_game_session(
        self,
        *,
        session_id: str,
        telegram_user_id: int,
        game_key: str,
        difficulty: str,
        prompt: str,
        options: list[str],
        correct_answer: str,
        reward_diamonds: int,
        expires_at: str,
    ) -> None:
        self._validate_user_id(telegram_user_id)
        if difficulty not in {"easy", "hard"} or not 0 <= reward_diamonds <= 100:
            raise ValueError("Invalid game configuration.")
        await self.ensure_account(telegram_user_id)
        await self._request(
            "POST",
            "fortunis8_game_sessions",
            json={
                "id": session_id,
                "telegram_user_id": telegram_user_id,
                "game_key": game_key,
                "difficulty": difficulty,
                "prompt": prompt[:300],
                "options": options[:6],
                "correct_answer": correct_answer[:50],
                "reward_diamonds": reward_diamonds,
                "expires_at": expires_at,
            },
            prefer="return=minimal",
        )

    async def complete_game(
        self, session_id: str, telegram_user_id: int, answer: str
    ) -> dict[str, Any]:
        self._validate_user_id(telegram_user_id)
        result = await self._rpc(
            "fortunis8_complete_game",
            {
                "p_session_id": session_id,
                "p_telegram_user_id": telegram_user_id,
                "p_answer": answer[:50],
            },
        )
        if not isinstance(result, dict):
            raise PersistenceError("Game result was invalid.")
        return result

    async def create_pending_invoice(
        self,
        *,
        payload: str,
        telegram_user_id: int,
        focus: str,
        amount_stars: int,
    ) -> None:
        self._validate_user_id(telegram_user_id)
        if focus not in {"general", "love", "work", "growth"} or amount_stars <= 0:
            raise ValueError("Invalid premium reading invoice.")
        await self.ensure_account(telegram_user_id)
        await self._request(
            "POST",
            "fortunis8_pending_invoices",
            json={
                "invoice_payload": payload,
                "telegram_user_id": telegram_user_id,
                "product": "premium_palm_reading",
                "focus": focus,
                "amount_stars": amount_stars,
                "currency": "XTR",
            },
            prefer="return=minimal",
        )

    async def get_valid_invoice(
        self, payload: str, telegram_user_id: int
    ) -> dict[str, Any] | None:
        self._validate_user_id(telegram_user_id)
        response = await self._request(
            "GET",
            "fortunis8_pending_invoices",
            params={
                "select": "amount_stars,currency,telegram_user_id,expires_at",
                "invoice_payload": f"eq.{payload}",
                "telegram_user_id": f"eq.{telegram_user_id}",
                "limit": "1",
            },
        )
        rows = self._decode_json(response)
        if not isinstance(rows, list) or (rows and not isinstance(rows[0], dict)):
            raise PersistenceError("Invoice record was invalid.")
        if not rows:
            return None
        record = rows[0]
        try:
            expiry = datetime.fromisoformat(str(record["expires_at"]).replace("Z", "+00:00"))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
        except (KeyError, TypeError, ValueError):
            raise PersistenceError("Invoice expiry was invalid.") from None
        if expiry <= datetime.now(timezone.utc):
            return None
        return record

    async def cancel_pending_invoice(self, payload: str, telegram_user_id: int) -> None:
        self._validate_user_id(telegram_user_id)
        await self._request(
            "DELETE",
            "fortunis8_pending_invoices",
            params={
                "invoice_payload": f"eq.{payload}",
                "telegram_user_id": f"eq.{telegram_user_id}",
            },
            prefer="return=minimal",
        )

    async def record_star_payment(
        self,
        telegram_user_id: int,
        payload: str,
        charge_id: str,
        amount: int,
        currency: str,
    ) -> dict[str, Any]:
        self._validate_user_id(telegram_user_id)
        result = await self._rpc(
            "fortunis8_record_star_payment",
            {
                "p_telegram_user_id": telegram_user_id,
                "p_invoice_payload": payload,
                "p_charge_id": charge_id,
                "p_amount": amount,
                "p_currency": currency,
            },
        )
        if not isinstance(result, dict):
            raise PersistenceError("Payment verification result was invalid.")
        return result

    async def redeem_premium_reading(
        self,
        telegram_user_id: int,
        focus: str,
        title: str,
        content: str,
    ) -> dict[str, Any]:
        self._validate_user_id(telegram_user_id)
        result = await self._rpc(
            "fortunis8_redeem_premium_reading",
            {
                "p_telegram_user_id": telegram_user_id,
                "p_focus": focus,
                "p_title": title[:120],
                "p_content": content[:3500],
            },
        )
        if not isinstance(result, dict):
            raise PersistenceError("Premium reading redemption result was invalid.")
        return result

    async def get_leaderboard(self, telegram_user_id: int) -> tuple[list[int], int | None]:
        self._validate_user_id(telegram_user_id)
        response = await self._request(
            "GET",
            ACCOUNTS_TABLE,
            params={"select": "diamonds", "order": "diamonds.desc", "limit": "10"},
        )
        rows = self._decode_json(response)
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise PersistenceError("Leaderboard response was invalid.")
        scores: list[int] = []
        for row in rows:
            value = row.get("diamonds")
            if isinstance(value, int) and value >= 0:
                scores.append(value)
        rank_result = await self._rpc(
            "fortunis8_get_rank", {"p_telegram_user_id": telegram_user_id}
        )
        rank = rank_result if isinstance(rank_result, int) else None
        return scores, rank
