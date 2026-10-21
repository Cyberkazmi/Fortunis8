from dataclasses import dataclass
from typing import Optional


@dataclass
class FortuneReading:
    user_id: str
    fortune_type: str  # horoscope, tarot, palm, general
    title: str
    content: str
    card_name: Optional[str] = None
    score: Optional[int] = None
    created_at: Optional[str] = None
