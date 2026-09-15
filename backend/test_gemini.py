from app.services.gemini_service import generate_caption

with open("test.jpg", "rb") as f:
    image_bytes = f.read()

# --- Test 1: single image, no context (should behave exactly like before) ---
print("\n=== TEST 1: single image, no context ===")
caption = generate_caption([(image_bytes, "image/jpeg")])
print(caption)

# --- Test 2: multiple images, no context (carousel mode) ---
print("\n=== TEST 2: multiple images (using test.jpg twice), no context ===")
caption = generate_caption([
    (image_bytes, "image/jpeg"),
    (image_bytes, "image/jpeg"),
])
print(caption)

# --- Test 3: single image, WITH context ---
print("\n=== TEST 3: single image, with context ===")
caption = generate_caption(
    [(image_bytes, "image/jpeg")],
    context="my graduation day",
)
print(caption)