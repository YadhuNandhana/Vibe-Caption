# Vibe Caption

An AI-powered Instagram caption generator built with Google Gemini. Upload one or
more photos, get back a witty, hashtag-ready caption — with a few extra features
layered on top: automatic privacy checks, AI-suggested songs, and local caption
history.

## Features

- **Smart captioning** — Upload 1–6 images. A single photo gets a caption written
  for it directly; multiple photos are treated as one cohesive "carousel" story,
  not separate captions per image.
- **Optional context** — Add a short note (e.g. "graduation day") to personalize
  the tone of the caption without it being repeated verbatim.
- **Drag-and-drop or click-to-upload** — supports both, mergeable across multiple
  selections, with individual image removal.
- **Privacy heads-up** — Before you post, the app checks all uploaded images for
  commonly-overshared details (readable documents, legible license plates, visible
  screens) — without flagging normal people or group photos. Runs automatically,
  no extra click needed, and never blocks captioning if the check itself fails.
- **Song suggestions** — On request, Gemini suggests songs matching the photo's
  mood, which are then verified against Apple's free iTunes Search API for real
  metadata, album art, and a 30-second preview clip.
- **Dominant color palette** — Extracts a small aesthetic color palette from your
  photo(s) using Pillow's built-in quantization (no external ML dependencies).
- **Caption history** — Every generated caption is saved locally in your browser
  (no account, no server-side storage) and can be deleted individually.

No login system, no paid/subscription services anywhere in the stack.

## Tech stack

**Frontend:** HTML5, CSS3 (custom design system, no framework), vanilla JavaScript,
`localStorage` for history, `<canvas>` for thumbnail generation.

**Backend:** Python, FastAPI, Uvicorn, python-dotenv, Pillow, `requests`.

**AI / external services:**
- [Google Gemini](https://ai.google.dev/) (`google-genai` SDK) — captioning, privacy
  analysis, and song-idea generation.
- [iTunes Search API](https://performance-partners.apple.com/search-api) — free,
  no auth — verifies song suggestions against a real catalog.

## Project structure

```
insta-caption-app/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint, CORS, route registration
│   │   ├── config.py                 # loads .env, exposes the Gemini API key
│   │   ├── routes/                   # HTTP endpoints (caption, songs, palette)
│   │   └── services/                 # Gemini calls, iTunes lookups, color extraction
│   ├── .env.example                  # template — copy to .env and add your own key
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

## Setup instructions

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/vibe-caption.git
cd vibe-caption
```

### 2. Set up the backend

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:
- **Windows (PowerShell):** `venv\Scripts\Activate.ps1`
- **macOS/Linux:** `source venv/bin/activate`

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Add your own Gemini API key

Copy the example env file and fill in your own key (get one free at
[Google AI Studio](https://aistudio.google.com/)):

```bash
cp .env.example .env
```

Then open `.env` and replace the placeholder with your real key:

```
GEMINI_API_KEY=your_actual_key_here
```

### 4. Run the backend

```bash
uvicorn app.main:app --reload
```

You should see `Uvicorn running on http://127.0.0.1:8000`. Visit
`http://127.0.0.1:8000/docs` to confirm the API is live and explore the endpoints.

### 5. Run the frontend

Open `frontend/index.html` directly in your browser (double-click it, or
right-click → Open with → your browser of choice). No build step or server needed.

## Notes

- Caption history is stored entirely in the browser (`localStorage`) — it's
  per-device and not synced anywhere.
- The privacy check is a best-effort heads-up, not a guarantee — it's designed to
  catch common accidental oversharing (documents, plates, screens) while
  deliberately avoiding false flags on normal people/group photos.
- If Gemini returns a 404/quota error referencing the model name, check
  [Google's model list](https://ai.google.dev/gemini-api/docs/models) for the
  current name and update the `MODEL_NAME` constant in `gemini_service.py`.