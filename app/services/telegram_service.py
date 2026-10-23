from __future__ import annotations

from app.services.ai_service import generate_fortune
from app.services.fortune_service import (
    DEFAULT_MOOD,
    DEFAULT_PERSONA,
    normalize_mood,
    normalize_persona,
)


def _persona_style(persona: str) -> str:
    persona = normalize_persona(persona)
    style_map = {
        "Oracle of Light": "speak with gentle wisdom, hope, and graceful clarity; the reading should feel warm and insightful.",
        "Sun Warrior": "speak with courage, confidence, and momentum; emphasize boldness and forward energy.",
        "Moon Reader": "speak with dreamy, intimate, emotional depth; emphasize intuition, reflection, and hidden emotional truths.",
        "Guardian of Fortune": "speak with protective guidance, grounded wisdom, and practical blessings.",
        "Shadow Seer": "speak with depth, honesty, and transformative insight; address shadows with courage and maturity.",
    }
    return style_map.get(persona, "speak with warm, mystical guidance and practical insight.")


def _mood_tone(mood: str) -> str:
    mood = normalize_mood(mood)
    tone_map = {
        "balanced": "keep the reading calm, thoughtful, steady and reassuring.",
        "hopeful": "focus on optimism, renewal, and a brighter next step.",
        "stressed": "acknowledge pressure and offer clear, grounding guidance with emotional care.",
        "lonely": "respond with warmth, companionship, and gentle encouragement.",
        "ambitious": "highlight momentum, strategy, and meaningful progress.",
        "sad": "offer compassionate, healing, and validating language without sounding dismissive.",
        "curious": "encourage exploration, discovery, and wonder while staying grounded.",
    }
    return tone_map.get(mood, "keep the message supportive and emotionally aware.")


def _build_fortune_prompt(sign: str, user_name: str, mood: str | None, persona: str | None, reading_type: str, question: str | None = None) -> str:
    persona = normalize_persona(persona or DEFAULT_PERSONA)
    mood = normalize_mood(mood or DEFAULT_MOOD)
    persona_style = _persona_style(persona)
    mood_tone = _mood_tone(mood)

    if reading_type == "tarot":
        question_text = question or "What should I focus on today?"
        return (
            f"Write a mystical tarot reading for {user_name}. "
            f"The user has zodiac sign {sign}. "
            f"Their current mood is {mood}. "
            f"Their persona is {persona}. "
            f"Use this tone: {persona_style} {mood_tone} "
            f"The question is: {question_text}. "
            "Keep the reading poetic, emotionally intelligent, and practical."
        )

    return (
        f"Write a daily horoscope for {user_name} with zodiac sign {sign}. "
        f"The user is currently feeling {mood}. "
        f"Their persona is {persona}. "
        f"Use this tone: {persona_style} {mood_tone} "
        "Make it uplifting, mystical, emotionally grounded, and specific to their current state."
    )


def generate_horoscope(sign: str, user_name: str = "Seeker", mood: str | None = None, persona: str | None = None) -> str:
    prompt = _build_fortune_prompt(sign, user_name, mood, persona, reading_type="horoscope")
    return generate_fortune(prompt, persona=normalize_persona(persona or DEFAULT_PERSONA))


def generate_tarot_reading(question: str, user_name: str = "Seeker", mood: str | None = None, persona: str | None = None) -> str:
    sign = "Aries"
    prompt = _build_fortune_prompt(sign, user_name, mood, persona, reading_type="tarot", question=question)
    return generate_fortune(prompt, persona=normalize_persona(persona or DEFAULT_PERSONA))


def generate_palm_reading(context: str, user_name: str = "Seeker", mood: str | None = None, persona: str | None = None) -> str:
    sign = "Aries"
    prompt = (
        f"Interpret a palm reading for {user_name} based on this description: {context}. "
        f"Their mood is {normalize_mood(mood or DEFAULT_MOOD)}. "
        f"Their persona is {normalize_persona(persona or DEFAULT_PERSONA)}. "
        "Keep it insightful, poetic, and supportive."
    )
    return generate_fortune(prompt, persona=normalize_persona(persona or DEFAULT_PERSONA))
