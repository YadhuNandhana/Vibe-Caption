from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.gemini_service import generate_caption, check_privacy_concerns
from app.services.gemini_service import generate_caption
from app.services.gemini_service import generate_caption_with_privacy

router = APIRouter()

MAX_IMAGES = 6


@router.post("/api/caption")
async def create_caption(
    files: list[UploadFile] = File(...),
    context: str | None = Form(None),
):
    # Must have at least one image
    if not files:
        raise HTTPException(status_code=400, detail="At least one image is required")

    # Cap how many images we'll accept in one carousel
    if len(files) > MAX_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Too many images — please upload at most {MAX_IMAGES}",
        )

    images: list[tuple[bytes, str]] = []

    for file in files:
        # Make sure each file is actually an image
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"'{file.filename}' is not a valid image file",
            )

        image_bytes = await file.read()

        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"'{file.filename}' is empty",
            )

        images.append((image_bytes, file.content_type))

    try:
        result = generate_caption_with_privacy(images, context)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini API error: {str(e)}")

    return {"caption": result["caption"], "privacy_notes": result["privacy_notes"]}