from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.palette_service import extract_palette, extract_combined_palette

router = APIRouter()

MAX_IMAGES = 6

@router.post("/api/palette")
async def get_palettes(files: list[UploadFile] = File(...)):
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="No images uploaded.")
    if len(files) > MAX_IMAGES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_IMAGES} images allowed.")

    for f in files:
        if not f.content_type or not f.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"{f.filename} is not an image file.")

    # Read every file's bytes once, reuse for both per-photo and combined palettes
    all_bytes = [await f.read() for f in files]

    for b in all_bytes:
        if len(b) == 0:
            raise HTTPException(status_code=400, detail="One of the uploaded files is empty.")

    per_photo = [extract_palette(b) for b in all_bytes]
    combined = extract_combined_palette(all_bytes) if len(all_bytes) > 1 else per_photo[0]

    return {
        "per_photo_palettes": per_photo,
        "combined_palette": combined
    }