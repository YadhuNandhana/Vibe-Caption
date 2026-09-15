import json
from app.services.gemini_service import client, MODEL_NAME, generate_caption, check_privacy_concerns
from google.genai import types

MERGED_PROMPT_TEMPLATE = (
    "{caption_instruction}"
    "{context_instruction}"
    "\n\nSEPARATELY, also check ALL of these images for details someone might not "
    "realize they're sharing publicly. Only flag things in these specific categories:\n"
    "1. Readable personal documents (mail, ID cards, boarding passes, shipping labels "
    "with visible names/addresses)\n"
    "2. Clearly legible license plates\n"
    "3. Screens showing visible private info (open messages, emails, personal apps)\n"
    "4. Bystanders who appear to be accidentally in frame, NOT people who are clearly "
    "the intentional subject of the photo (do NOT flag people posing together, group "
    "photos, selfies, or friends who are the point of the picture)\n\n"
    "Respond ONLY with valid JSON, no other text, no markdown formatting, in exactly "
    "this shape:\n"
    '{{"caption": "the caption text here", "privacy_notes": '
    '[{{"concern": "short label", "detail": "one specific sentence"}}]}}\n'
    "If nothing privacy-related is found, use an empty list for privacy_notes."
)

SINGLE_CAPTION_INSTRUCTION = (
    "Look at this image and write a witty, engaging Instagram caption for it. "
    "Include relevant emojis and 3-5 relevant hashtags. "
    "Keep it short — 1 to 3 sentences before the hashtags."
)

CAROUSEL_CAPTION_INSTRUCTION = (
    "Look at these images together. They are a set of photos from ONE single "
    "Instagram carousel post — the same event, trip, or moment. Write ONE witty, "
    "cohesive Instagram caption that ties the whole set together as a single "
    "connected story — NOT a separate caption per photo. Include relevant emojis "
    "and 3-5 relevant hashtags. Keep it short — 1 to 3 sentences before the hashtags."
)

CONTEXT_INSTRUCTION = (
    " The user has given this extra context: \"{context}\". Use it to shape the "
    "tone/story, but do NOT just repeat it word-for-word."
)


def generate_caption_with_privacy(images: list[tuple[bytes, str]], context: str | None = None) -> dict:
    """
    ONE Gemini call that returns both the caption AND privacy concerns,
    checked across ALL provided images. Falls back to the original two
    separate, proven functions if parsing ever fails.
    """
    caption_instruction = SINGLE_CAPTION_INSTRUCTION if len(images) == 1 else CAROUSEL_CAPTION_INSTRUCTION
    context_instruction = CONTEXT_INSTRUCTION.format(context=context.strip()) if context and context.strip() else ""

    prompt = MERGED_PROMPT_TEMPLATE.format(
        caption_instruction=caption_instruction,
        context_instruction=context_instruction,
    )

    contents = [
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        for image_bytes, mime_type in images
    ]
    contents.append(prompt)

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=contents)
        raw_text = response.text.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            raw_text = raw_text.replace("json", "", 1).strip()

        result = json.loads(raw_text)

        # Sanity check the shape is what we expect
        if "caption" not in result or "privacy_notes" not in result:
            raise ValueError("Missing expected fields in merged response")

        return result

    except Exception as e:
        print(f"Merged call failed ({e}), falling back to two separate calls...")
        caption = generate_caption(images, context)
        first_bytes, first_mime = images[0]
        privacy_notes = check_privacy_concerns(first_bytes, first_mime)
        return {"caption": caption, "privacy_notes": privacy_notes}


if __name__ == "__main__":
    with open("test2.jpg", "rb") as f:
        image_a = f.read()

    with open("test.jpg", "rb") as f:
        image_b = f.read()

    print("\n=== Clean carousel test: two normal photos, nothing sensitive ===")
    # Swap these two filenames below for whichever TWO photos you have that
    # are genuinely clean — e.g. people posing, scenery, food, etc.
    # (If test.jpg/test2.jpg both have license plates in them, grab a
    # different pair of clean photos instead so this is a fair test.)
    result = generate_caption_with_privacy([
        (image_a, "image/jpeg"),
        (image_b, "image/jpeg"),
    ])
    print(json.dumps(result, indent=2))