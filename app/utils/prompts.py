FORTUNE_SYSTEM_PROMPT = """
You are a mystical AI fortune teller for Fortunis8.
Speak with memory, warmth, wonder, and practical insight.
Your tone should feel personal yet magical.
"""


def build_fortune_prompt(user_name: str, category: str, question: str) -> str:
    return (
        f"User: {user_name}\n"
        f"Category: {category}\n"
        f"Question: {question}\n\n"
        "Provide a poetic but actionable response."
    )
