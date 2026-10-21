def award_diamonds(current_balance: int, amount: int) -> int:
    return current_balance + amount


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
