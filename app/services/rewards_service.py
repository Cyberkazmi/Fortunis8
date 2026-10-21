def award_diamonds(current_balance: int, amount: int) -> int:
    return current_balance + amount


WELCOME_REWARD_DIAMONDS = 25
DAILY_REWARD_DIAMONDS = 10


def apply_welcome_reward(current_balance: int) -> int:
    return award_diamonds(current_balance, WELCOME_REWARD_DIAMONDS)


def update_level(diamonds: int) -> int:
    if diamonds >= 500:
        return 5
    if diamonds >= 250:
        return 4
    if diamonds >= 100:
        return 3
    if diamonds >= 50:
        return 2
    return 1


def award_diamonds_and_level(current_balance: int, amount: int) -> tuple[int, int]:
    new_balance = award_diamonds(current_balance, amount)
    return new_balance, update_level(new_balance)
