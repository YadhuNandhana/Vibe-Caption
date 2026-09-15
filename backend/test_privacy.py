import json
from google import genai
from google.genai import types
from app.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL_NAME = "gemini-3.5-flash-lite"

PRIVACY_CHECK_PROMPT = (
    "Look at this image and check for details someone might not realize they're "
    "sharing publicly. Only flag things in these specific categories:\n"
    "1. Readable personal documents (mail, ID cards, boarding passes, shipping labels "
    "with visible names/addresses)\n"
    "2. Clearly legible license plates\n"
    "3. Screens showing visible private info (open messages, emails, personal apps)\n"
    "4. Bystanders who appear to be accidentally in frame, NOT people who are "
    "clearly the intentional subject of the photo (e.g. do NOT flag people posing "
    "together, group photos, selfies, or friends who are the point of the picture)\n\n"
    "If nothing in these categories is present, return an empty list.\n\n"
    "Respond ONLY with valid JSON, no other text, no markdown formatting, in exactly "
    "this shape:\n"
    '[{"concern": "short label", "detail": "one specific sentence about what was found"}]'
)


def check_privacy_concerns(image_bytes: bytes, mime_type: str) -> list[dict]:
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            PRIVACY_CHECK_PROMPT,
        ],
    )

    raw_text = response.text.strip()

    # Strip markdown code fences if Gemini adds them despite instructions
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json", "", 1).strip()

    try:
        concerns = json.loads(raw_text)
    except json.JSONDecodeError:
        print("Could not parse Gemini's response as JSON. Raw response was:")
        print(raw_text)
        return []

    return concerns


if __name__ == "__main__":
    with open("test.jpg", "rb") as f:
        image_bytes = f.read()

    concerns = check_privacy_concerns(image_bytes, "image/jpeg")

    if not concerns:
        print("\nNo concerns flagged — looks good to post.\n")
    else:
        print(f"\nFound {len(concerns)} thing(s) worth double-checking:\n")
        for c in concerns:
            print(f"- {c['concern']}: {c['detail']}")
        print()