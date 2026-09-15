import requests

URL = "http://127.0.0.1:8000/api/caption"


def run_test(name, filenames, context=None):
    print(f"\n=== {name} ===")

    files = [
        ("files", (fname, open(fname, "rb"), "image/jpeg"))
        for fname in filenames
    ]
    data = {"context": context} if context else {}

    response = requests.post(URL, files=files, data=data)

    print("Status code:", response.status_code)
    print("Response:", response.json())

    # Close the opened files
    for _, (_, f, _) in files:
        f.close()


# Test 1: single image, no context
run_test("Test 1: single image, no context", ["test.jpg"])

# Test 2: single image, with context
run_test("Test 2: single image, with context", ["test.jpg"], context="my graduation day")

# Test 3: multiple images, no context
run_test("Test 3: multiple images, no context", ["test.jpg", "test.jpg"])

# Test 4: multiple images, with context
run_test(
    "Test 4: multiple images, with context",
    ["test.jpg", "test.jpg"],
    context="reunion trip with my best friends",
)