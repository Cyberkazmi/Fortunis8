from dataclasses import dataclass
from typing import Optional


@dataclass
class UserProfile:
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    zodiac_sign: Optional[str] = None
    selected_persona: Optional[str] = None
    diamonds: int = 0
    streak_count: int = 0
    level: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
