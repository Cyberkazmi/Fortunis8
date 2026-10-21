from __future__ import annotations

from openai import OpenAI

from app.config import settings


def get_openai_client() -> OpenAI:
    settings.validate_ai()
    return OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30.0)


def generate_fortune(prompt: str, *, persona: str = "mystical guide") -> str:
    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a mystical AI fortune teller for Fortunis8. "
                    "Speak with wonder, warmth, and precise insight. "
                    "Keep answers emotionally rich and encouraging."
                ),
            },
            {
                "role": "user",
                "content": f"Persona: {persona}\nPrompt: {prompt}",
            },
        ],
        temperature=0.9,
        max_tokens=600,
    )
    return response.choices[0].message.content.strip()
