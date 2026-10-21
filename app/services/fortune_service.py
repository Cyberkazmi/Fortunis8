from app.services.ai_service import generate_fortune


def generate_horoscope(sign: str, user_name: str = "Seeker") -> str:
    prompt = (
        f"Write a daily horoscope for {user_name} with zodiac sign {sign}. "
        "Make it uplifting, mystical, and emotionally grounded."
    )
    return generate_fortune(prompt, persona="celestial oracle")


def generate_tarot_reading(question: str, user_name: str = "Seeker") -> str:
    prompt = (
        f"{user_name} asks: {question}. "
        "Present a tarot-style reading with symbolism, guidance, and a practical takeaway."
    )
    return generate_fortune(prompt, persona="tarot reader")


def generate_palm_reading(context: str, user_name: str = "Seeker") -> str:
    prompt = (
        f"Interpret a palm reading for {user_name} based on this description: {context}. "
        "Keep it insightful, poetic, and supportive."
    )
    return generate_fortune(prompt, persona="palm reader")
