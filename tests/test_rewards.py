from app.services.rewards_service import award_diamonds, update_level


def test_award_diamonds() -> None:
    assert award_diamonds(20, 10) == 30


def test_update_level() -> None:
    assert update_level(0) == 1
    assert update_level(50) == 2
    assert update_level(100) == 3
