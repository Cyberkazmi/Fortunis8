from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class RitualCompletion:
    user_id: str
    stable_key: str
    completed_for: date
    xp_awarded: int
    diamonds_awarded: int
    already_completed: bool = False


class InMemoryCompletionRepository:
    """Local test repository; production persistence belongs in ritual_activity and ledgers."""

    def __init__(self) -> None:
        self._completed: set[tuple[str, str, date]] = set()

    def complete(self, user_id: str, stable_key: str, completed_for: date) -> RitualCompletion:
        key = (user_id, stable_key, completed_for)
        if key in self._completed:
            return RitualCompletion(user_id, stable_key, completed_for, 0, 0, already_completed=True)
        self._completed.add(key)
        return RitualCompletion(user_id, stable_key, completed_for, 40, 20)

    def clear(self) -> None:
        self._completed.clear()
