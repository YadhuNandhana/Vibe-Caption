import json
from google import genai
from google.genai import types
from app.config import settings
import requests

client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL_NAME = "gemini-3.5-flash-lite"
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"

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


def _get_gemini_suggestions(images: list[tuple[bytes, str]], caption: str, context: str | None, language: str):
    prompt = f"""
You are a music curator for Instagram posts. Based on the photo(s), the caption,
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

    contents = [
        types.Part.from_bytes(data=image_bytes, mime_type=content_type)
        for image_bytes, content_type in images
    ]
    contents.append(prompt)

    response = client.models.generate_content(model=MODEL_NAME, contents=contents)
    raw_text = response.text.strip()

    try:
        suggestions = json.loads(raw_text)
    except json.JSONDecodeError:
        # Gemini didn't return clean JSON this time — treat it as "no
        # suggestions" rather than crashing the whole request.
        print(f"[song_service] Failed to parse Gemini JSON. Raw output:\n{raw_text}")
        return []

    if not isinstance(suggestions, list):
        return []

    return suggestions


def _find_song(title: str, artist: str, country: str):
    query = f"{title} {artist}"
    params = {
        "term": query,
        "media": "music",
        "entity": "song",
        "limit": 5,
        "country": country,
    }

    try:
        response = requests.get(ITUNES_SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"[song_service] iTunes request failed for '{query}': {e}")
        return None

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


def get_verified_songs(images: list[tuple[bytes, str]], caption: str, context: str | None, language: str):
    suggestions = _get_gemini_suggestions(images, caption, context, language)
    country = LANGUAGE_TO_COUNTRY.get(language, "US")

    verified_songs = []
    for suggestion in suggestions:
        # Defensive check in case Gemini's JSON is missing expected keys
        title = suggestion.get("title")
        artist = suggestion.get("artist")
        reason = suggestion.get("reason", "")
        if not title or not artist:
            continue

        match = _find_song(title, artist, country=country)
        if match is None:
            continue

        verified_songs.append({
            "title": match["title"],
            "artist": match["artist"],
            "album_art": match["album_art"],
            "preview_url": match["preview_url"],
            "reason": reason,
        })

    return verified_songs