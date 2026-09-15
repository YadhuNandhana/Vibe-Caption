import json
from google import genai
from google.genai import types
from app.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

MODEL_NAME = "gemini-3.5-flash-lite"

def suggest_songs(caption: str, context: str, image_path: str, language: str):
    prompt = f"""
You are a music curator for Instagram posts. Based on the photo, the caption,
and optional context below, suggest 3 to 5 real songs performed/sung in
{language} that match the overall MOOD and VIBE (not literal objects in the
photo — e.g. a beach photo should NOT just get songs with "beach" in the
title).

All suggested songs MUST be in {language}. Do not suggest songs in any other
language.

Caption: {caption}
Context: {context if context else "(none provided)"}

Reply with ONLY a valid JSON array. No markdown, no code fences, no extra
text before or after. Each item must have exactly these keys:
- "title": the song title (string)
- "artist": the artist name (string)
- "reason": one short sentence (max 15 words) on why it fits the vibe

Example format:
[{{"title": "Song Name", "artist": "Artist Name", "reason": "Why it fits."}}]
"""

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            prompt,
        ],
    )

    raw_text = response.text.strip()
    print("----- RAW GEMINI OUTPUT -----")
    print(raw_text)
    print("------------------------------")

    songs = json.loads(raw_text)
    return songs


if __name__ == "__main__":
    result = suggest_songs(
        caption="Golden hour on the coast, salt in my hair and no plans to leave 🌅🌊",
        context="just moved to a beach town, feeling free",
        image_path="test.jpg",
        language="Malayalam",
    )
    print(f"\nPARSED SONGS:")
    for song in result:
        print(f"- {song['title']} by {song['artist']} → {song['reason']}")