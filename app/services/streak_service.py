from datetime import date, datetime, timedelta

from app.services.rewards_service import award_diamonds_and_level


def apply_daily_reward(profile: dict, context_data: dict | None = None) -> dict:
    """Apply daily reward logic once per user per day.

    This keeps the daily reward system lightweight and compatible with the current schema.
    It stores the current date in Telegram context memory rather than requiring a new DB column.
    """
    today = date.today().isoformat()
    current_balance = int(profile.get("diamonds", 0) or 0)
    current_streak = int(profile.get("streak_count", 0) or 0)
    last_daily_date = (context_data or {}).get("last_daily_date")

    if last_daily_date == today:
        return {
            "reward_earned": 0,
            "message": "You already claimed today's Fortunis8 reward.",
            "profile": profile,
            "new_last_daily_date": today,
        }

    if last_daily_date:
        try:
            last_date_obj = datetime.strptime(last_daily_date, "%Y-%m-%d").date()
            if last_date_obj == date.today() - timedelta(days=1):
                new_streak = current_streak + 1
            else:
                new_streak = 1
        except ValueError:
            new_streak = 1
    else:
        new_streak = 1

    reward_amount = 10 + max(0, new_streak - 1) * 5
    updated_balance, updated_level = award_diamonds_and_level(current_balance, reward_amount)

    updated_profile = dict(profile)
    updated_profile["diamonds"] = updated_balance
    updated_profile["streak_count"] = new_streak
    updated_profile["level"] = updated_level

    return {
        "reward_earned": reward_amount,
        "message": (
            f"Daily reward claimed: +{reward_amount} diamonds. "
            f"Current streak: {new_streak}."
        ),
        "profile": updated_profile,
        "new_last_daily_date": today,
    }
