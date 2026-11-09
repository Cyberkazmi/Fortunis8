import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.bot.fortunis8_handlers import (
    _horoscope_input_parts,
    daily_command,
    fortune_command,
    horoscope_input,
    pre_checkout,
    route_callback,
    start,
    start_game,
    successful_payment,
)


class FakeStore:
    def __init__(self):
        self.get_or_create_language = AsyncMock(return_value="en")
        self.ensure_account = AsyncMock()
        self.get_account = AsyncMock(return_value={
            "diamonds": 15,
            "level": 1,
            "streak_count": 2,
            "selected_persona": "Wizard",
            "premium_reading_credits": 1,
        })
        self.save_reading = AsyncMock()
        self.create_game_session = AsyncMock()
        self.claim_daily = AsyncMock(return_value={"ok": True, "claimed": True, "reward": 2, "streak": 3, "diamonds": 17})
        self.get_valid_invoice = AsyncMock(return_value={"amount_stars": 25, "currency": "XTR"})
        self.record_star_payment = AsyncMock(return_value={"ok": True, "credited": True, "focus": "work"})
        self.redeem_premium_reading = AsyncMock(return_value={"ok": True, "credits_remaining": 0})

    async def close(self):
        pass


def make_update(*, text="", chat_type="private", user_id=42, callback=None, payment=None, update_id=77):
    message = SimpleNamespace(text=text, reply_text=AsyncMock(), successful_payment=payment)
    if callback is not None:
        callback.message = message
    return SimpleNamespace(
        update_id=update_id,
        effective_user=SimpleNamespace(id=user_id, first_name="Reader"),
        effective_chat=SimpleNamespace(type=chat_type, id=123),
        effective_message=message,
        message=message,
        callback_query=callback,
        pre_checkout_query=None,
    )


def make_context(store, language="en"):
    return SimpleNamespace(
        user_data={"fortunis8_language": language},
        application=SimpleNamespace(bot_data={"fortunis8_store": store}),
        bot=SimpleNamespace(send_invoice=AsyncMock()),
        args=[],
    )


class Fortunis8HandlerTests(unittest.TestCase):
    def test_horoscope_format_accepts_comma_and_returns_only_transient_birth_fields(self):
        birth_date, birth_time, location = _horoscope_input_parts("1990-07-23 08:30, Karachi")
        self.assertEqual(str(birth_date), "1990-07-23")
        self.assertEqual(birth_time.strftime("%H:%M"), "08:30")
        self.assertEqual(location, "Karachi")

    def test_horoscope_rejects_future_date(self):
        from datetime import date
        with self.assertRaises(OverflowError):
            _horoscope_input_parts(f"{date.today().replace(year=date.today().year + 1)} 08:30, Lahore")

    def test_start_persists_default_language_and_creates_account(self):
        store = FakeStore()
        update = make_update()
        context = make_context(store)
        asyncio.run(start(update, context))
        store.get_or_create_language.assert_awaited_once_with(42)
        store.ensure_account.assert_awaited_once_with(42)
        self.assertIn("Welcome to Fortunis8", update.effective_message.reply_text.await_args.args[0])

    def test_horoscope_persists_reading_but_not_birth_details(self):
        store = FakeStore()
        update = make_update(text="1990-07-23 08:30, Karachi")
        context = make_context(store, "ur")
        context.user_data["fortunis8_awaiting_horoscope"] = True
        result = asyncio.run(horoscope_input(update, context))
        self.assertIsNone(result)
        self.assertNotIn("fortunis8_awaiting_horoscope", context.user_data)
        store.save_reading.assert_awaited_once()
        saved_args = store.save_reading.await_args.args
        saved_kwargs = store.save_reading.await_args.kwargs
        self.assertNotIn("1990-07-23", str(saved_args) + str(saved_kwargs))
        self.assertNotIn("08:30", str(saved_args) + str(saved_kwargs))
        self.assertNotIn("Karachi", str(saved_args) + str(saved_kwargs))
        self.assertIn("تفریح", update.effective_message.reply_text.await_args.args[0])

    def test_fortune_saves_disclaimer_and_reports_persistence(self):
        store = FakeStore()
        update = make_update()
        context = make_context(store)
        asyncio.run(fortune_command(update, context))
        store.save_reading.assert_awaited_once()
        self.assertIn("not a guaranteed prediction", update.effective_message.reply_text.await_args.args[0])

    def test_game_session_is_created_with_higher_reward_for_hard_mode(self):
        store = FakeStore()
        update = make_update()
        context = make_context(store)
        asyncio.run(start_game(update, context, "easy"))
        easy_reward = store.create_game_session.await_args.kwargs["reward_diamonds"]
        store.create_game_session.reset_mock()
        asyncio.run(start_game(update, context, "hard"))
        hard_reward = store.create_game_session.await_args.kwargs["reward_diamonds"]
        self.assertGreater(hard_reward, easy_reward)
        self.assertEqual(hard_reward, 50)

    def test_pre_checkout_accepts_only_saved_matching_star_invoice(self):
        store = FakeStore()
        query = SimpleNamespace(
            invoice_payload="fortunis8:42:payload",
            from_user=SimpleNamespace(id=42),
            currency="XTR",
            total_amount=25,
            answer=AsyncMock(),
        )
        update = make_update()
        update.pre_checkout_query = query
        context = make_context(store)
        asyncio.run(pre_checkout(update, context))
        query.answer.assert_awaited_once_with(ok=True)

    def test_successful_payment_is_verified_and_premium_reading_is_atomic(self):
        store = FakeStore()
        payment = SimpleNamespace(
            invoice_payload="fortunis8:42:payload",
            telegram_payment_charge_id="charge-1",
            total_amount=25,
            currency="XTR",
        )
        update = make_update(payment=payment, update_id=901)
        context = make_context(store)
        asyncio.run(successful_payment(update, context))
        store.record_star_payment.assert_awaited_once_with(42, "fortunis8:42:payload", "charge-1", 25, "XTR")
        store.redeem_premium_reading.assert_awaited_once()
        self.assertEqual(store.redeem_premium_reading.await_args.args[:3], (42, 901, "work"))
        self.assertIn("Your detailed reading is below", update.effective_message.reply_text.await_args_list[-1].args[0])

    def test_duplicate_premium_update_reuses_update_id_without_resending_a_reading(self):
        store = FakeStore()
        store.redeem_premium_reading.side_effect = [
            {"ok": True, "duplicate": False, "credits_remaining": 0},
            {"ok": True, "duplicate": True, "credits_remaining": 0},
        ]
        callback = SimpleNamespace(data="palm:focus:use:work", answer=AsyncMock())
        update = make_update(callback=callback, update_id=902)
        context = make_context(store)

        asyncio.run(route_callback(update, context))
        update.effective_message.reply_text.reset_mock()
        asyncio.run(route_callback(update, context))

        self.assertEqual(store.redeem_premium_reading.await_count, 2)
        self.assertEqual(
            [call.args[1] for call in store.redeem_premium_reading.await_args_list],
            [902, 902],
        )
        self.assertEqual(len(update.effective_message.reply_text.await_args_list), 1)
        self.assertIn("already processed", update.effective_message.reply_text.await_args.args[0])

    def test_daily_reward_calls_server_side_idempotent_rpc(self):
        store = FakeStore()
        update = make_update()
        context = make_context(store)
        asyncio.run(daily_command(update, context))
        store.claim_daily.assert_awaited_once_with(42)
        self.assertIn("+2 diamonds", update.effective_message.reply_text.await_args.args[0])


if __name__ == "__main__":
    unittest.main()
