from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.song_service import get_verified_songs

router = APIRouter()

MAX_IMAGES = 6
ALLOWED_LANGUAGES = {"Tamil", "English", "Hindi", "Telugu", "Malayalam", "Spanish", "Kannada", "French"}


@router.post("/api/songs")
async def suggest_songs(
    files: list[UploadFile] = File(...),
    caption: str = Form(...),
    context: str | None = Form(None),
    language: str = Form(...),
):
    if not files:
        raise HTTPException(status_code=400, detail="At least one image is required")

    if len(files) > MAX_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Too many images — please upload at most {MAX_IMAGES}",
        )

    if language not in ALLOWED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"'{language}' is not a supported language",
        )

    images: list[tuple[bytes, str]] = []

    for file in files:
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
        songs = get_verified_songs(images, caption, context, language)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Song suggestion error: {str(e)}")

    return {"songs": songs}