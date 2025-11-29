# ai_roast.py
import os
from typing import List, Optional
from openai import OpenAI

# Reads OPENAI_API_KEY from env (Railway / Replit / local)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_roast(
    author_name: str,
    user_message: str,
    history_lines: Optional[List[str]] = None,
) -> str:
    """
    Returns a short, playful roast string.

    author_name: display name of user to roast
    user_message: what they just said
    history_lines: recent chat lines like "Name: message"
    """

    if history_lines:
        history_text = "\n".join(history_lines[-10:])
    else:
        history_text = "No previous context."

    prompt = f"""
You are a playful Discord roast bot in a gaming server.

Rules:
- Light, witty, sarcastic roasts.
- No slurs, no insults about race, gender, religion, sexuality, disability, or appearance.
- Focus on brain, skill issue, game sense, bad takes, etc.
- MAX 25 words.
- ONE line only. No markdown.

Recent channel messages:
{history_text}

User to roast: {author_name}
They just said: {user_message}

Now answer with ONE short roast line.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",   # cheap but good, change if you want
        input=prompt,
        max_output_tokens=60,
    )

    return response.output_text.strip()
