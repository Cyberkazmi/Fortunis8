from app.services.ai_service import generate_fortune


def test_generate_fortune_returns_text() -> None:
    result = generate_fortune("Give me a hopeful fortune for today.")
    assert isinstance(result, str)
    assert len(result) > 20
