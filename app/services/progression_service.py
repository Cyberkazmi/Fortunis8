from __future__ import annotations

from copy import deepcopy
from typing import Any


PROTOTYPE_QUESTS = [
    {
        "key": "daily_ritual",
        "title": "Complete today's ritual",
        "description": "Finish the small practice selected for your path.",
        "xp": 40,
        "diamonds": 10,
    },
    {
        "key": "goal_checkin",
        "title": "Name your next step",
        "description": "Write one concrete action for your chosen goal.",
        "xp": 20,
        "diamonds": 5,
    },
    {
        "key": "reflection_note",
        "title": "Save a reflection",
        "description": "Note one thing you noticed after today's action.",
        "xp": 25,
        "diamonds": 8,
    },
]


def new_progression() -> dict[str, Any]:
    return {
        "xp": 0,
        "diamonds": 0,
        "level": 1,
        "streak": 0,
        "quests": {
            quest["key"]: {**quest, "status": "active"}
            for quest in PROTOTYPE_QUESTS
        },
    }


def _level_for_xp(xp: int) -> int:
    return max(1, (int(xp) // 100) + 1)


def complete_prototype_quest(
    progression: dict[str, Any] | None, quest_key: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    state = deepcopy(progression or new_progression())
    key = (quest_key or "").strip().lower()
    quest = state["quests"].get(key)

    if quest is None:
        return state, {
            "completed": False,
            "message": "I could not find that prototype quest. Use /quests to see the available keys.",
        }

    if quest["status"] == "completed":
        return state, {
            "completed": False,
            "quest": quest,
            "message": f"Already complete: {quest['title']}. Choose another quest when you are ready.",
        }

    quest["status"] = "completed"
    state["xp"] += int(quest["xp"])
    state["diamonds"] += int(quest["diamonds"])
    state["level"] = _level_for_xp(state["xp"])
    if key == "daily_ritual":
        state["streak"] = max(1, int(state.get("streak", 0)) + 1)

    return state, {
        "completed": True,
        "quest": quest,
        "message": (
            f"Quest complete: {quest['title']}\n"
            f"+{quest['xp']} XP · +{quest['diamonds']} diamonds\n"
            f"Level {state['level']} · {state['xp']} XP total · {state['streak']} day streak"
        ),
    }


def format_progression_summary(progression: dict[str, Any] | None) -> str:
    state = progression or new_progression()
    lines = [
        "Your path quests:",
        f"Progress: Level {state['level']} · {state['xp']} XP · {state['diamonds']} diamonds · {state['streak']} day streak",
    ]
    for quest in state["quests"].values():
        status = "✅ complete" if quest["status"] == "completed" else "⏳ active"
        lines.append(f"- /done {quest['key']} — {quest['title']} [{status}]")
    return "\n".join(lines)
