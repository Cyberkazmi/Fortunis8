from dataclasses import dataclass
from typing import Optional


@dataclass
class Reward:
    user_id: str
    source: str
    amount: int
    reason: str
    created_at: Optional[str] = None
