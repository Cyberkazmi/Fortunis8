import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import httpx

from app.db.fortunis8_store import PersistenceError, SupabaseRestUserStore


TEST_SECRET = "sb_secret_fixture"


class StoreTests(unittest.IsolatedAsyncioTestCase):
    async def test_language_api_key_is_not_sent_as_authorization(self):
        requests = []

        async def handler(request):
            requests.append(request)
            return httpx.Response(200, json=[{"language": "ur"}])

        client = httpx.AsyncClient(
            base_url="https://example.supabase.co/rest/v1/",
            transport=httpx.MockTransport(handler),
        )
        store = SupabaseRestUserStore("https://example.supabase.co", TEST_SECRET, client=client)
        try:
            self.assertEqual(await store.get_or_create_language(1234), "ur")
        finally:
            await client.aclose()
        self.assertEqual(requests[0].headers["apikey"], TEST_SECRET)
        self.assertNotIn("authorization", requests[0].headers)
        self.assertEqual(requests[0].url.path, "/rest/v1/fortunis8_users")

    async def test_create_game_session_sends_only_the_bound_challenge(self):
        seen = []

        async def handler(request):
            seen.append(request)
            return httpx.Response(201)

        client = httpx.AsyncClient(
            base_url="https://example.supabase.co/rest/v1/",
            transport=httpx.MockTransport(handler),
        )
        store = SupabaseRestUserStore("https://example.supabase.co", TEST_SECRET, client=client)
        store.ensure_account = AsyncMock()
        try:
            await store.create_game_session(
                session_id="00000000-0000-4000-8000-000000000001",
                telegram_user_id=11,
                game_key="arithmetic",
                difficulty="hard",
                prompt="144 square root?",
                options=["10", "12", "14"],
                correct_answer="12",
                reward_diamonds=50,
                expires_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            )
        finally:
            await client.aclose()
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].url.path, "/rest/v1/fortunis8_game_sessions")
        self.assertEqual(seen[0].headers["apikey"], TEST_SECRET)
        body = json.loads(seen[0].read())
        self.assertEqual(body["correct_answer"], "12")
        self.assertEqual(body["options"], ["10", "12", "14"])

    async def test_rpc_result_is_decoded_and_star_payment_payload_is_exact(self):
        seen = []

        async def handler(request):
            seen.append(request)
            return httpx.Response(200, json={"ok": True, "credited": True, "focus": "work"})

        client = httpx.AsyncClient(
            base_url="https://example.supabase.co/rest/v1/",
            transport=httpx.MockTransport(handler),
        )
        store = SupabaseRestUserStore("https://example.supabase.co", TEST_SECRET, client=client)
        try:
            result = await store.record_star_payment(77, "payload", "charge", 25, "XTR")
        finally:
            await client.aclose()
        self.assertTrue(result["credited"])
        self.assertEqual(seen[0].url.path, "/rest/v1/rpc/fortunis8_record_star_payment")
        self.assertEqual(json.loads(seen[0].read()), {
            "p_telegram_user_id": 77, "p_invoice_payload": "payload",
            "p_charge_id": "charge", "p_amount": 25, "p_currency": "XTR",
        })

    async def test_invalid_invoice_returns_none_and_no_response_body_is_exposed(self):
        async def handler(request):
            return httpx.Response(200, json=[])

        client = httpx.AsyncClient(
            base_url="https://example.supabase.co/rest/v1/",
            transport=httpx.MockTransport(handler),
        )
        store = SupabaseRestUserStore("https://example.supabase.co", TEST_SECRET, client=client)
        try:
            self.assertIsNone(await store.get_valid_invoice("missing", 8))
        finally:
            await client.aclose()

        async def bad_handler(request):
            return httpx.Response(401, text="private provider error")

        client2 = httpx.AsyncClient(
            base_url="https://example.supabase.co/rest/v1/",
            transport=httpx.MockTransport(bad_handler),
        )
        store2 = SupabaseRestUserStore("https://example.supabase.co", TEST_SECRET, client=client2)
        try:
            with self.assertRaises(PersistenceError) as caught:
                await store2.get_or_create_language(8)
        finally:
            await client2.aclose()
        self.assertNotIn("private provider error", str(caught.exception))
        self.assertNotIn(TEST_SECRET, str(caught.exception))

    async def test_invalid_ids_and_game_rewards_are_rejected(self):
        client = httpx.AsyncClient(
            base_url="https://example.supabase.co/rest/v1/",
            transport=httpx.MockTransport(lambda request: httpx.Response(201)),
        )
        store = SupabaseRestUserStore("https://example.supabase.co", TEST_SECRET, client=client)
        try:
            with self.assertRaises(ValueError):
                await store.get_or_create_language(-1)
            with self.assertRaises(ValueError):
                await store.create_game_session(
                    session_id="00000000-0000-4000-8000-000000000002",
                    telegram_user_id=2,
                    game_key="arithmetic",
                    difficulty="hard",
                    prompt="Q?",
                    options=["1"],
                    correct_answer="1",
                    reward_diamonds=101,
                    expires_at="2026-11-09T00:00:00+00:00",
                )
        finally:
            await client.aclose()


if __name__ == "__main__":
    unittest.main()
