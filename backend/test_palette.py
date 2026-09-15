from PIL import Image
from sklearn.cluster import KMeans
import numpy as np

def get_palette(image_path, n_colors=5):
    # Open the image and make sure it's plain RGB (no transparency channel, etc.)
    img = Image.open(image_path).convert("RGB")

    # Shrink it — we don't need every pixel, just a representative sample
    img = img.resize((150, 150))

    # Turn the image into a flat list of [R, G, B] pixel values
    pixels = np.array(img).reshape(-1, 3)

    # Ask k-means to find n_colors "clumps" of similar colors
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    kmeans.fit(pixels)

    # The clump centers ARE the dominant colors (as RGB floats) — round and convert to int
    centers = kmeans.cluster_centers_.astype(int)

    # Convert each [R, G, B] into a hex string like "#f4a261"
    hex_colors = ["#{:02x}{:02x}{:02x}".format(r, g, b) for r, g, b in centers]

    return hex_colors

def get_combined_palette(image_paths, n_colors=5):
    all_pixels = []

    for path in image_paths:
        img = Image.open(path).convert("RGB")
        img = img.resize((150, 150))  # same size for every photo = equal weighting
        pixels = np.array(img).reshape(-1, 3)
        all_pixels.append(pixels)

    # Stack all photos' pixels into one big pile
    combined_pixels = np.vstack(all_pixels)

    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    kmeans.fit(combined_pixels)

    centers = kmeans.cluster_centers_.astype(int)
    hex_colors = ["#{:02x}{:02x}{:02x}".format(r, g, b) for r, g, b in centers]

    return hex_colors

if __name__ == "__main__":
    palette = get_palette("test.jpg")
    print("Dominant palette for test.jpg:")
    for color in palette:
        print(" ", color)

    combined = get_combined_palette(["test.jpg", "test2.jpg"])
    print("\nCombined palette for test.jpg + test2.jpg:")
    for color in combined:
        print(" ", color)