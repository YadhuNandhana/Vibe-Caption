import json
from google import genai
from google.genai import types
from app.config import settings
import requests

client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL_NAME = "gemini-3.5-flash-lite"
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"

# Maps each dropdown language to an iTunes storefront country code that's
# likely to have good coverage for that language.
LANGUAGE_TO_COUNTRY = {
    "Tamil": "IN",
    "English": "US",
    "Hindi": "IN",
    "Telugu": "IN",
    "Malayalam": "IN",
    "Spanish": "ES",
    "Kannada": "IN",
    "French": "FR",
}


def get_gemini_suggestions(caption: str, context: str, image_path: str, language: str):
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
    return json.loads(raw_text)


def find_song(title: str, artist: str, country: str = "US"):
    query = f"{title} {artist}"
    params = {
        "term": query,
        "media": "music",
        "entity": "song",
        "limit": 5,
        "country": country,
    }

    response = requests.get(ITUNES_SEARCH_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    results = data.get("results", [])
    if not results:
        return None

    best = None
    for r in results:
        result_artist = r.get("artistName", "").lower()
        if artist.lower() in result_artist or result_artist in artist.lower():
            best = r
            break

    if best is None:
        best = results[0]

    return {
        "title": best.get("trackName"),
        "artist": best.get("artistName"),
        "album_art": best.get("artworkUrl100"),
        "preview_url": best.get("previewUrl"),
    }


def get_verified_songs(caption: str, context: str, image_path: str, language: str):
    gemini_suggestions = get_gemini_suggestions(caption, context, image_path, language)
    country = LANGUAGE_TO_COUNTRY.get(language, "US")

    verified_songs = []
    for suggestion in gemini_suggestions:
        match = find_song(suggestion["title"], suggestion["artist"], country=country)
        if match is None:
            print(f"  [dropped] No iTunes match for: {suggestion['title']} by {suggestion['artist']}")
            continue

        verified_songs.append({
            "title": match["title"],
            "artist": match["artist"],
            "album_art": match["album_art"],
            "preview_url": match["preview_url"],
            "reason": suggestion["reason"],
        })

    return verified_songs


if __name__ == "__main__":
    songs = get_verified_songs(
        caption="Golden hour on the coast, salt in my hair and no plans to leave 🌅🌊",
        context="just moved to a beach town, feeling free",
        image_path="test.jpg",
        language="Spanish",
    )

    print(f"\n{len(songs)} VERIFIED SONGS:")
    for s in songs:
        preview = s["preview_url"] or "(no preview available)"
        print(f"- {s['title']} by {s['artist']}")
        print(f"    Reason: {s['reason']}")
        print(f"    Album art: {s['album_art']}")
        print(f"    Preview: {preview}")