from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any


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


class SupabaseCompletionRepository:
    """Service-role adapter with idempotency enforced by database keys."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def complete(self, user_id: str, stable_key: str, completed_for: date) -> RitualCompletion:
        key = f"{user_id}:{completed_for.isoformat()}:{stable_key}"
        existing = self.client.table("ritual_assignments").select("id,status").eq("idempotency_key", key).limit(1).execute().data or []
        if existing and existing[0].get("status") == "completed":
            return RitualCompletion(user_id, stable_key, completed_for, 0, 0, already_completed=True)
        ritual_rows = self.client.table("ritual_catalog").select("id,content_version").eq("stable_key", stable_key).limit(1).execute().data or []
        if not ritual_rows:
            raise ValueError("Ritual is not present in the live catalog")
        ritual = ritual_rows[0]
        assignment = self.client.table("ritual_assignments").upsert(
            {
                "user_id": user_id,
                "ritual_id": ritual["id"],
                "ritual_content_version": ritual["content_version"],
                "assigned_for_local_date": completed_for.isoformat(),
                "slot_key": "daily",
                "status": "assigned",
                "source": "mvp",
                "idempotency_key": key,
            },
            on_conflict="idempotency_key",
        ).execute().data or []
        assignment_id = assignment[0]["id"] if assignment else None
        if assignment_id is None:
            raise RuntimeError("Supabase assignment upsert returned no row")
        self.client.table("ritual_assignments").update({"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}).eq("id", assignment_id).execute()
        self.client.table("ritual_activity").insert({"assignment_id": assignment_id, "user_id": user_id, "event_type": "completed"}).execute()
        self.client.table("xp_ledger").upsert({"user_id": user_id, "source_type": "ritual", "source_id": assignment_id, "amount": 40, "idempotency_key": key}).execute()
        self.client.table("diamond_ledger").upsert({"user_id": user_id, "source_type": "ritual", "source_id": assignment_id, "amount": 20, "reason": "ritual_completion", "idempotency_key": key}).execute()
        return RitualCompletion(user_id, stable_key, completed_for, 40, 20)
