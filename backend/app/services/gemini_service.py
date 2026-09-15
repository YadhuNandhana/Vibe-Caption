from google import genai
from google.genai import types
from app.config import settings

# Create one client, reused for every request
client = genai.Client(api_key=settings.GEMINI_API_KEY)

MODEL_NAME = "gemini-3.5-flash-lite"

SINGLE_IMAGE_PROMPT = (
    "Look at this image and write a witty, engaging Instagram caption for it. "
    "Include relevant emojis and 3-5 relevant hashtags. "
    "Keep it short — 1 to 3 sentences before the hashtags."
)

CAROUSEL_PROMPT = (
    "Look at these images together. They are a set of photos from ONE single "
    "Instagram carousel post — the same event, trip, or moment. "
    "Write ONE witty, cohesive Instagram caption that ties the whole set together "
    "as a single connected story. Do NOT describe each photo separately, and do "
    "NOT write a list of mini-captions — write it as one unified post. "
    "Include relevant emojis and 3-5 relevant hashtags. "
    "Keep it short — 1 to 3 sentences before the hashtags."
)

CONTEXT_INSTRUCTION = (
    " The user has given this extra context about the photo(s): \"{context}\". "
    "Use this context to shape the tone, feeling, or story of the caption — but do "
    "NOT just repeat the context text word-for-word in your output."
)


def generate_caption(images: list[tuple[bytes, str]], context: str | None = None) -> str:
    """
    Takes a list of images and returns a generated Instagram-style caption.

    images: a list of (image_bytes, mime_type) tuples. Must contain at least one image.
            If it contains exactly one image, this behaves like the original
            single-image captioning. If it contains more than one, Gemini is
            instructed to write one cohesive "carousel" caption across all of them.
    context: optional short text from the user (e.g. "graduation day"). If None or
             empty, captioning is based purely on the image(s), same as before.
    """
    if not images:
        raise ValueError("generate_caption requires at least one image.")

    # Pick the right base instruction depending on how many images we got
    if len(images) == 1:
        prompt = SINGLE_IMAGE_PROMPT
    else:
        prompt = CAROUSEL_PROMPT

    # If the user gave context, tack on an extra instruction
    if context and context.strip():
        prompt += CONTEXT_INSTRUCTION.format(context=context.strip())

    # Build the contents list: all image parts first, then the text prompt
    contents = [
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        for image_bytes, mime_type in images
    ]
    contents.append(prompt)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
    )
    return response.text
import json

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
    """
    Checks one image for common accidental-privacy-share concerns
    (documents, license plates, visible screens, accidental bystanders).
    Returns an empty list if nothing is found or if the check fails —
    this is a best-effort helper, not a hard requirement for captioning to work.
    """
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                PRIVACY_CHECK_PROMPT,
            ],
        )

        raw_text = response.text.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            raw_text = raw_text.replace("json", "", 1).strip()

        return json.loads(raw_text)

    except Exception as e:
        # If this fails for any reason (bad JSON, API hiccup), don't break
        # captioning over it — just report no concerns found.
        print(f"Privacy check failed silently: {e}")
        return []

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


def generate_caption_with_privacy(images: list[tuple[bytes, str]], context: str | None = None) -> dict:
    """
    ONE Gemini call that returns both the caption AND privacy concerns,
    checked across ALL provided images. Falls back to the original two
    separate, proven functions if parsing ever fails.
    """
    caption_instruction = SINGLE_IMAGE_PROMPT if len(images) == 1 else CAROUSEL_PROMPT
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

        if "caption" not in result or "privacy_notes" not in result:
            raise ValueError("Missing expected fields in merged response")

        return result

    except Exception as e:
        print(f"Merged call failed ({e}), falling back to two separate calls...")
        caption = generate_caption(images, context)
        first_bytes, first_mime = images[0]
        privacy_notes = check_privacy_concerns(first_bytes, first_mime)
        return {"caption": caption, "privacy_notes": privacy_notes}