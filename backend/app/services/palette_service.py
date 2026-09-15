from PIL import Image
import io


def _load_image(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _get_dominant_colors(image: Image.Image, num_colors: int = 5) -> list[str]:
    """
    Reduces the image to its most dominant colors using Pillow's built-in
    quantization (median cut algorithm) — no scikit-learn/scipy needed.
    Returns hex color strings, most dominant (most pixels) first.
    """
    small = image.copy()
    small.thumbnail((150, 150))

    quantized = small.quantize(colors=num_colors, method=Image.MEDIANCUT)

    color_counts = quantized.getcolors(maxcolors=small.width * small.height)
    palette = quantized.getpalette()

    color_counts.sort(reverse=True, key=lambda item: item[0])

    hex_colors = []
    for count, palette_index in color_counts[:num_colors]:
        r = palette[palette_index * 3]
        g = palette[palette_index * 3 + 1]
        b = palette[palette_index * 3 + 2]
        hex_colors.append(_rgb_to_hex((r, g, b)))

    return hex_colors


def extract_palette(image_bytes: bytes, num_colors: int = 5) -> list[str]:
    """Extracts the dominant color palette from a single image."""
    image = _load_image(image_bytes)
    return _get_dominant_colors(image, num_colors)


def extract_combined_palette(images: list[bytes], num_colors: int = 5) -> list[str]:
    """
    Extracts ONE combined palette across multiple images (e.g. a carousel),
    by stitching small thumbnails side-by-side into one canvas first.
    """
    thumbnails = []
    for image_bytes in images:
        img = _load_image(image_bytes)
        img.thumbnail((150, 150))
        thumbnails.append(img)

    total_width = sum(img.width for img in thumbnails)
    max_height = max(img.height for img in thumbnails)

    combined = Image.new("RGB", (total_width, max_height))
    x_offset = 0
    for img in thumbnails:
        combined.paste(img, (x_offset, 0))
        x_offset += img.width

    return _get_dominant_colors(combined, num_colors)