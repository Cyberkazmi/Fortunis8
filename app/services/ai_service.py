from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_fortune(prompt: str, *, persona: str = "mystical guide") -> str:
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
