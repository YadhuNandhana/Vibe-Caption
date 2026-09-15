import requests

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"


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

    # Simple "best match" strategy: prefer a result where the artist name
    # roughly matches what we searched for (case-insensitive substring check).
    best = None
    for r in results:
        result_artist = r.get("artistName", "").lower()
        if artist.lower() in result_artist or result_artist in artist.lower():
            best = r
            break

    # Fallback: if no artist matched closely, just take the first result.
    if best is None:
        best = results[0]

    return {
        "title": best.get("trackName"),
        "artist": best.get("artistName"),
        "album_art": best.get("artworkUrl100"),
        "preview_url": best.get("previewUrl"),  # may be None — that's OK
    }


if __name__ == "__main__":
    test_cases = [
        ("Shape of You", "Ed Sheeran"),
        ("Vaathi Coming", "Anirudh Ravichander"),
        ("Definitely Maybe Nonexistent Song XYZ123", "Fake Artist"),
    ]

    for title, artist in test_cases:
        print(f"\nSearching: '{title}' by '{artist}'")
        result = find_song(title, artist)
        if result is None:
            print("  -> No match found (correctly returned None)")
        else:
            print(f"  -> Matched: {result['title']} by {result['artist']}")
            print(f"     Album art: {result['album_art']}")
            print(f"     Preview URL: {result['preview_url']}")