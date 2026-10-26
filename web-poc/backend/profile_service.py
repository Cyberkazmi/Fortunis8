from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
from typing import Any


BELIEF_MODES = {"Scientific", "Mindfulness", "Spiritual", "Religious", "Practical", "Mixed"}
CATALOG_MODE_FOR_BELIEF = {
    "Scientific": "scientific",
    "Mindfulness": "mindfulness",
    "Spiritual": "spiritual_reflection",
    "Religious": "religious_practice",
    "Practical": "practical",
    "Mixed": "mixed",
}
GOALS = {
    "business_wealth", "study_exams", "career_interview", "health_energy", "stress_calm",
    "relationships", "creativity", "discipline", "spiritual_reflection", "religious_routine",
    "confidence", "life_transition", "sleep_recovery",
}
RHYTHMS = {2, 5, 10}


@dataclass(frozen=True)
class UserProfile:
    user_id: str
    goals: tuple[str, ...]
    belief_mode: str
    rhythm_minutes: int
    language: str
    optional_readings: bool = False
    delivery_time: str | None = None
    timezone: str | None = None


class ProfileRepository:
    def __init__(self) -> None:
        self._profiles: dict[str, UserProfile] = {}

    def save(self, profile: UserProfile) -> UserProfile:
        self._profiles[profile.user_id] = profile
        return profile

    def get(self, user_id: str) -> UserProfile | None:
        return self._profiles.get(str(user_id))


@dataclass(frozen=True)
class Ritual:
    stable_key: str
    title: str
    description: str
    guidance_mode: str
    duration_seconds: int
    goals: frozenset[str]


# This is the in-memory representation of the existing 28-row catalog seed.
RITUAL_CATALOG = [
    Ritual("box_breath_4", "Box breathing, 2 minutes", "Breathe in for 4, hold 4, out 4, hold 4. Repeat 6 rounds. Then name one thing you will do next.", "mindfulness", 120, frozenset({"stress_calm", "study_exams", "career_interview"})),
    Ritual("long_exhale", "Longer exhale", "Inhale through the nose for 4, exhale slowly for 6 to 8. Ten rounds.", "scientific", 90, frozenset({"stress_calm", "sleep_recovery"})),
    Ritual("one_priority", "One priority", "Write the single task that would make today a win. Add when and where you will start it.", "practical", 180, frozenset({"discipline", "business_wealth", "study_exams", "career_interview"})),
    Ritual("if_then_plan", "If-then plan", "Complete: If it is [time/place], then I will [small action]. Keep the action under 5 minutes.", "scientific", 180, frozenset({"discipline", "health_energy", "study_exams"})),
    Ritual("focus_block_25", "25-minute focus block", "Silence your phone, set a 25-minute timer, work on one thing only. Note what you finished.", "scientific", 1500, frozenset({"study_exams", "creativity", "business_wealth"})),
    Ritual("active_recall", "Active recall", "Close your notes. Write everything you remember about one topic, then check and mark gaps.", "scientific", 600, frozenset({"study_exams"})),
    Ritual("money_check", "5-minute money check", "Review yesterday's income and spending. Write one decision for today.", "practical", 300, frozenset({"business_wealth"})),
    Ritual("customer_reachout", "One reach-out", "Send one useful message to a customer, colleague or contact. Keep it short and specific.", "motivational", 600, frozenset({"business_wealth", "career_interview"})),
    Ritual("star_story", "STAR story", "Write one achievement as Situation, Task, Action, Result. Practise saying it aloud once.", "practical", 420, frozenset({"career_interview", "confidence"})),
    Ritual("evidence_list", "Evidence list", "Write three things you handled well this month. Next to each, the skill it shows.", "scientific", 240, frozenset({"confidence", "life_transition"})),
    Ritual("reframe_thought", "Reframe one thought", "Write a worrying thought. Ask: what is another way to see this? Write a balanced version.", "scientific", 300, frozenset({"stress_calm", "confidence"})),
    Ritual("gratitude_three", "Three gratitudes", "Write three specific things you are grateful for today and why each matters.", "spiritual_reflection", 180, frozenset({"spiritual_reflection", "stress_calm", "relationships"})),
    Ritual("evening_review", "Evening review", "What went well? What will I do differently tomorrow? One line each.", "mixed", 300, frozenset({"discipline", "spiritual_reflection", "life_transition"})),
    Ritual("intention_morning", "Morning intention", "Write one word for how you want to show up today and one action that proves it.", "motivational", 120, frozenset({"confidence", "discipline", "creativity"})),
    Ritual("faith_routine_check", "Faith routine check-in", "Following your own tradition, note one practice you want to keep today and the time you will do it.", "religious_practice", 180, frozenset({"religious_routine", "spiritual_reflection"})),
    Ritual("kind_message", "One kind message", "Send a short, genuine message of appreciation to someone.", "practical", 180, frozenset({"relationships"})),
    Ritual("listen_fully", "Listen fully", "In your next conversation, listen without planning your reply. Afterwards note one thing you learned.", "mindfulness", 300, frozenset({"relationships"})),
    Ritual("idea_capture", "Idea capture", "Write 10 rough ideas on one problem in 5 minutes. Circle one to try.", "practical", 300, frozenset({"creativity", "business_wealth"})),
    Ritual("make_small", "Make something small", "Spend 15 minutes making anything: a sketch, a paragraph, a tune. Done beats perfect.", "motivational", 900, frozenset({"creativity"})),
    Ritual("walk_10", "10-minute walk", "Take a 10-minute walk, outdoors if you can. Notice five things you see.", "scientific", 600, frozenset({"health_energy", "stress_calm", "creativity"})),
    Ritual("stretch_5", "Gentle 5-minute stretch", "Neck, shoulders, back and legs, slowly, with easy breathing. No pain.", "mindfulness", 300, frozenset({"health_energy", "sleep_recovery"})),
    Ritual("water_habit", "Water anchor", "Drink a glass of water now and link the next glass to a meal.", "practical", 60, frozenset({"health_energy"})),
    Ritual("wind_down", "Wind-down", "Dim lights, put the phone away, and write tomorrow's first task so your mind can let go.", "scientific", 600, frozenset({"sleep_recovery", "stress_calm"})),
    Ritual("body_scan", "Body scan", "Lying down, move attention slowly from toes to head, relaxing each area.", "mindfulness", 420, frozenset({"sleep_recovery", "stress_calm"})),
    Ritual("next_step_visual", "See the next step", "Close your eyes and picture yourself doing the next step: where, when, the first move. Then do the first move.", "visualization", 180, frozenset({"career_interview", "confidence", "business_wealth"})),
    Ritual("transition_anchor", "Steady anchor", "Write what is changing, what stays the same, and one routine you will keep this week.", "mixed", 300, frozenset({"life_transition"})),
    Ritual("streak_promise", "Two-minute promise", "Pick a habit and do just two minutes of it now. Keep the streak, not the pressure.", "motivational", 60, frozenset({"discipline"})),
    Ritual("reading_reflect", "Optional reading as reflection", "Draw your optional reading (tarot, horoscope or palm prompt). Ask: what does this invite me to notice today? Write one action.", "mixed", 240, frozenset({"spiritual_reflection", "creativity", "confidence"})),
]


def choose_ritual(profile: UserProfile, user_id: str, on_date: date | None = None) -> dict[str, Any]:
    day = on_date or date.today()
    selected_goals = set(profile.goals)
    mode = CATALOG_MODE_FOR_BELIEF[profile.belief_mode]
    max_seconds = profile.rhythm_minutes * 60

    def eligible(guidance_mode: str) -> list[Ritual]:
        return sorted(
            [r for r in RITUAL_CATALOG if r.guidance_mode == guidance_mode and r.duration_seconds <= max_seconds and r.goals & selected_goals],
            key=lambda r: r.stable_key,
        )

    candidates = eligible(mode)
    fallback_used = False
    if not candidates and mode != "practical":
        candidates = eligible("practical")
        fallback_used = True
    if not candidates:
        candidates = sorted([r for r in RITUAL_CATALOG if r.duration_seconds <= max_seconds and r.goals & selected_goals], key=lambda r: r.stable_key)
    if not candidates:
        raise ValueError("No catalog ritual matches the selected goals and rhythm")

    digest = hashlib.sha256(f"{user_id}:{day.isoformat()}".encode()).digest()
    ritual = candidates[int.from_bytes(digest[:8], "big") % len(candidates)]
    return {
        "stable_key": ritual.stable_key,
        "title": ritual.title,
        "description": ritual.description,
        "guidance_mode": ritual.guidance_mode,
        "duration_minutes": max(1, round(ritual.duration_seconds / 60)),
        "goals": sorted(ritual.goals & selected_goals),
        "action_step": "Take the smallest useful action described above now.",
        "fallback_used": fallback_used,
        "date": day.isoformat(),
    }
