from app.services.palette_service import extract_palette, extract_combined_palette

with open("test.jpg", "rb") as f:
    test_bytes = f.read()

with open("test2.jpg", "rb") as f:
    test2_bytes = f.read()

print("Single photo palette:")
for c in extract_palette(test_bytes):
    print(" ", c)

print("\nCombined palette:")
for c in extract_combined_palette([test_bytes, test2_bytes]):
    print(" ", c)