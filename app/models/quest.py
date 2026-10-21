from dataclasses import dataclass
from typing import Optional


@dataclass
class Quest:
    user_id: str
    quest_type: str
    title: str
    description: str
    status: str = "active"
    reward_diamonds: int = 0
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
