// Grab references to the HTML elements we defined by id
const uploadZone = document.getElementById("uploadZone");
const fileInput = document.getElementById("fileInput");
const previewGrid = document.getElementById("previewGrid");
const uploadPrompt = document.getElementById("uploadPrompt");
const generateBtn = document.getElementById("generateBtn");
const contextInput = document.getElementById("contextInput");

const MAX_IMAGES = 6;

// This will hold the array of selected files, so later steps can send them to the backend
let selectedFiles = [];

// 1) Clicking anywhere on the dropzone opens the native file picker
uploadZone.addEventListener("click", () => {
  fileInput.click();
});

// 2) When the user picks files, merge them into the existing selection,
//    validate, show previews, and enable the button
fileInput.addEventListener("change", () => {
  handleNewFiles(fileInput.files);
  fileInput.value = ""; // reset so picking the same file again still fires "change"
});

function handleNewFiles(fileList) {
  const newFiles = Array.from(fileList);

  if (newFiles.length === 0) {
    return; // nothing selected/dropped, do nothing
  }

  // Validation: every newly added file must be an image
  const nonImage = newFiles.find(f => !f.type.startsWith("image/"));
  if (nonImage) {
    alert(`"${nonImage.name}" is not an image file. Please only select images.`);
    return;
  }

  // Merge new files with whatever was already selected
  const combined = [...selectedFiles, ...newFiles];

  // Validation: total count (old + new) can't exceed the max
  if (combined.length > MAX_IMAGES) {
    alert(`You can select at most ${MAX_IMAGES} images total (you already have ${selectedFiles.length}).`);
    return;
  }

  selectedFiles = combined;
  renderThumbnails();

  previewGrid.hidden = false;
  uploadPrompt.hidden = true;
  generateBtn.disabled = false;
}
// Drag-and-drop support
["dragenter", "dragover"].forEach(eventName => {
  uploadZone.addEventListener(eventName, (event) => {
    event.preventDefault(); // stop the browser from opening the file directly
    uploadZone.classList.add("drag-active");
  });
});

["dragleave", "drop"].forEach(eventName => {
  uploadZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    uploadZone.classList.remove("drag-active");
  });
});

uploadZone.addEventListener("drop", (event) => {
  handleNewFiles(event.dataTransfer.files);
});

function renderThumbnails() {
  previewGrid.innerHTML = "";

  selectedFiles.forEach((file, index) => {
    const wrap = document.createElement("div");
    wrap.className = "thumb-wrap";

    const img = document.createElement("img");
    img.src = URL.createObjectURL(file);

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "thumb-remove";
    removeBtn.textContent = "×";
    removeBtn.setAttribute("aria-label", `Remove ${file.name}`);
    removeBtn.addEventListener("click", (event) => {
      event.stopPropagation(); // don't let this click bubble up and reopen the file picker
      removeImage(index);
    });

    wrap.appendChild(img);
    wrap.appendChild(removeBtn);
    previewGrid.appendChild(wrap);
  });
}

function removeImage(index) {
  selectedFiles.splice(index, 1);

  if (selectedFiles.length === 0) {
    // Back to the empty state
    previewGrid.hidden = true;
    previewGrid.innerHTML = "";
    uploadPrompt.hidden = false;
    generateBtn.disabled = true;
  } else {
    renderThumbnails();
  }
}

// ---------- Step 6.2: connect to backend ----------

const resultCard = document.getElementById("resultCard");
const statusLabel = document.getElementById("statusLabel");
const captionText = document.getElementById("captionText");
const tagRow = document.getElementById("tagRow");
const copyBtn = document.getElementById("copyBtn");
const songsNote = document.getElementById("songsNote");
const privacyNote = document.getElementById("privacyNote");
const privacyList = document.getElementById("privacyList");
const languageSelect = document.getElementById("languageSelect");
const songsBtn = document.getElementById("songsBtn");
const songList = document.getElementById("songList");

const BACKEND_URL = "http://127.0.0.1:8000/api/caption";

generateBtn.addEventListener("click", async () => {
  if (selectedFiles.length === 0) {
    return; // safety check, shouldn't happen since button is disabled until files are picked
  }

  // Show the result card in a "loading" state
  resultCard.hidden = false;
  statusLabel.textContent = "writing...";
  captionText.textContent = "";
  tagRow.innerHTML = "";
  copyBtn.hidden = true;
  songsNote.hidden = true;
  songList.hidden = true;
  songList.innerHTML = "";
  privacyNote.hidden = true;

  // While we wait, disable the button so it can't be clicked twice
  generateBtn.disabled = true;
  generateBtn.textContent = "Thinking...";

  try {
    // Build a FormData object — this is how browsers send files over HTTP
    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append("files", file);
    });

    // Only send context if the user actually typed something
    const contextValue = contextInput.value.trim();
    if (contextValue) {
      formData.append("context", contextValue);
    }

    const response = await fetch(BACKEND_URL, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error (${response.status})`);
    }

   const data = await response.json();
    lastCaptionFull = data.caption;
    displayResult(data.caption);
    addToHistory(data.caption, selectedFiles[0]);
    displayPrivacyNotes(data.privacy_notes);
  } catch (error) {
    statusLabel.textContent = "something went wrong";
    captionText.textContent = error.message;
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = "Find my caption";
  }
});

function displayResult(fullCaption) {
  statusLabel.textContent = "here's your caption";

  // Split hashtags (e.g. "#sunset") from the rest of the caption text
  const words = fullCaption.split(" ");
  const hashtags = words.filter(w => w.startsWith("#"));
  const mainText = words.filter(w => !w.startsWith("#")).join(" ").trim();

  captionText.textContent = mainText;

  tagRow.innerHTML = "";
  hashtags.forEach(tag => {
    const span = document.createElement("span");
    span.textContent = tag;
    tagRow.appendChild(span);
  });

  copyBtn.hidden = false;
  songsNote.hidden = false;
  paletteSection.hidden = false;
}

function displayPrivacyNotes(concerns) {
  if (!concerns || concerns.length === 0) {
    privacyNote.hidden = true;
    privacyList.innerHTML = "";
    return;
  }

  privacyList.innerHTML = "";
  concerns.forEach(item => {
    const li = document.createElement("li");
    li.textContent = item.detail;
    privacyList.appendChild(li);
  });

  privacyNote.hidden = false;
}
copyBtn.addEventListener("click", () => {
  const fullText = captionText.textContent + " " +
    Array.from(tagRow.querySelectorAll("span")).map(s => s.textContent).join(" ");

  navigator.clipboard.writeText(fullText.trim());
  copyBtn.textContent = "Copied!";
  setTimeout(() => { copyBtn.textContent = "Copy it"; }, 1500);
});
// ---------- Song suggestions ----------
const paletteBtn = document.getElementById("paletteBtn");
const paletteSection = document.getElementById("paletteSection");
const paletteResults = document.getElementById("paletteResults");
const PALETTE_BACKEND_URL = "http://127.0.0.1:8000/api/palette";

const SONGS_BACKEND_URL = "http://127.0.0.1:8000/api/songs";

let lastCaptionFull = "";   // full caption text (with hashtags) from the last successful generation
let currentAudio = null;    // tracks whichever preview clip is currently playing, so we can pause it

songsBtn.addEventListener("click", async () => {
  if (selectedFiles.length === 0 || !lastCaptionFull) {
    return; // safety check, shouldn't happen since the button only shows after a caption exists
  }

  songList.hidden = false;
  songList.innerHTML = `<p class="song-status">finding songs...</p>`;
  songsBtn.disabled = true;

  try {
    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append("files", file);
    });
    formData.append("caption", lastCaptionFull);

    const contextValue = contextInput.value.trim();
    if (contextValue) {
      formData.append("context", contextValue);
    }

    formData.append("language", languageSelect.value);

    const response = await fetch(SONGS_BACKEND_URL, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error (${response.status})`);
    }

    const data = await response.json();
    displaySongs(data.songs);

  } catch (error) {
    songList.innerHTML = `<p class="song-status">${error.message}</p>`;
  } finally {
    songsBtn.disabled = false;
  }
});

function displaySongs(songs) {
  songList.innerHTML = "";

  if (!songs || songs.length === 0) {
    songList.innerHTML = `<p class="song-status">couldn't find matching songs this time — try again?</p>`;
    return;
  }

  songs.forEach(song => {
    const item = document.createElement("div");
    item.className = "song-item";

    const art = document.createElement("img");
    art.className = "song-art";
    art.src = song.album_art || "";
    art.alt = "";

    const info = document.createElement("div");
    info.className = "song-info";

    const title = document.createElement("p");
    title.className = "song-title";
    title.textContent = song.title;

    const artist = document.createElement("p");
    artist.className = "song-artist";
    artist.textContent = song.artist;

    const reason = document.createElement("p");
    reason.className = "song-reason";
    reason.textContent = song.reason;

    info.appendChild(title);
    info.appendChild(artist);
    info.appendChild(reason);

    item.appendChild(art);
    item.appendChild(info);

    // Only add a play button if iTunes actually returned a preview clip —
    // this is the "hide gracefully" behavior for songs without one
    if (song.preview_url) {
      const playBtn = document.createElement("button");
      playBtn.type = "button";
      playBtn.className = "song-play";
      playBtn.textContent = "▶";
      playBtn.addEventListener("click", () => togglePreview(song.preview_url, playBtn));
      item.appendChild(playBtn);
    }

    songList.appendChild(item);
  });
}

function togglePreview(previewUrl, btn) {
  // If this exact clip is already playing, pause it
  if (currentAudio && currentAudio.src === previewUrl && !currentAudio.paused) {
    currentAudio.pause();
    btn.textContent = "▶";
    return;
  }

  // Stop whatever else was playing, and reset every play button's icon
  if (currentAudio) {
    currentAudio.pause();
  }
  document.querySelectorAll(".song-play").forEach(b => b.textContent = "▶");

  currentAudio = new Audio(previewUrl);
  currentAudio.play();
  btn.textContent = "⏸";

  currentAudio.addEventListener("ended", () => {
    btn.textContent = "▶";
  });
}

// ---------- Caption history (stored in the browser via localStorage) ----------

const HISTORY_KEY = "vibeCaptionHistory";
const MAX_HISTORY_ITEMS = 30; // keep storage from growing forever

const historySection = document.getElementById("historySection");
const historyList = document.getElementById("historyList");

function getHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (error) {
    console.error("Could not read caption history:", error);
    return [];
  }
}

function saveHistory(historyArray) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(historyArray));
  } catch (error) {
    console.error("Could not save caption history:", error);
  }
}

// Shrinks the first selected image down to a small compressed thumbnail
// (as a data URL string) so it's cheap to store in localStorage.
function makeThumbnail(file, maxSize = 96, quality = 0.6) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(maxSize / img.width, maxSize / img.height, 1);
      const canvas = document.createElement("canvas");
      canvas.width = img.width * scale;
      canvas.height = img.height * scale;

      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      resolve(canvas.toDataURL("image/jpeg", quality));
      URL.revokeObjectURL(img.src);
    };
    img.onerror = reject;
    img.src = URL.createObjectURL(file);
  });
}

async function addToHistory(fullCaption, imageFile) {
  const words = fullCaption.split(" ");
  const hashtags = words.filter(w => w.startsWith("#"));
  const mainText = words.filter(w => !w.startsWith("#")).join(" ").trim();

  let thumbnail = "";
  try {
    thumbnail = await makeThumbnail(imageFile);
  } catch (error) {
    console.error("Could not generate history thumbnail:", error);
  }

  const entry = {
    id: crypto.randomUUID(),
    caption: mainText,
    hashtags,
    thumbnail,
    timestamp: Date.now(),
  };

  const history = getHistory();
  history.unshift(entry); // newest first

  // Cap total stored entries so localStorage doesn't grow unbounded
  const trimmed = history.slice(0, MAX_HISTORY_ITEMS);

  saveHistory(trimmed);
  renderHistory();
}

function deleteHistoryItem(id) {
  const history = getHistory().filter(entry => entry.id !== id);
  saveHistory(history);
  renderHistory();
}

function formatTimestamp(ms) {
  const date = new Date(ms);
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  }) + " · " + date.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
}

function renderHistory() {
  const history = getHistory();

  if (history.length === 0) {
    historySection.hidden = true;
    historyList.innerHTML = "";
    return;
  }

  historySection.hidden = false;
  historyList.innerHTML = "";

  history.forEach(entry => {
    const item = document.createElement("div");
    item.className = "history-item";

    const thumb = document.createElement("img");
    thumb.className = "history-thumb";
    thumb.src = entry.thumbnail || "";
    thumb.alt = "";

    const content = document.createElement("div");
    content.className = "history-content";

    const captionP = document.createElement("p");
    captionP.className = "history-caption";
    captionP.textContent = entry.caption;

    const tagsP = document.createElement("p");
    tagsP.className = "history-tags";
    tagsP.textContent = entry.hashtags.join(" ");

    const timeP = document.createElement("p");
    timeP.className = "history-time";
    timeP.textContent = formatTimestamp(entry.timestamp);

    content.appendChild(captionP);
    if (entry.hashtags.length > 0) content.appendChild(tagsP);
    content.appendChild(timeP);

    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "history-delete";
    deleteBtn.textContent = "delete";
    deleteBtn.addEventListener("click", () => deleteHistoryItem(entry.id));

    item.appendChild(thumb);
    item.appendChild(content);
    item.appendChild(deleteBtn);
    historyList.appendChild(item);
  });
}

// Load and display any existing history as soon as the page opens
renderHistory();
// ---------- Color palette ----------

paletteBtn.addEventListener("click", async () => {
  if (selectedFiles.length === 0) {
    return;
  }

  paletteBtn.disabled = true;
  paletteBtn.textContent = "Loading...";

  try {
    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append("files", file);
    });

    const response = await fetch(PALETTE_BACKEND_URL, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error (${response.status})`);
    }

    const data = await response.json();
    renderPalettes(data.per_photo_palettes, data.combined_palette);
  } catch (error) {
    paletteResults.innerHTML = `<p class="song-status">${error.message}</p>`;
  } finally {
    paletteBtn.disabled = false;
    paletteBtn.textContent = "🎨 Show color palette";
  }
});

function renderPalettes(perPhotoPalettes, combinedPalette) {
  paletteResults.innerHTML = "";

  perPhotoPalettes.forEach((palette, index) => {
    paletteResults.appendChild(buildPaletteRow(`Photo ${index + 1}`, palette));
  });

  if (perPhotoPalettes.length > 1) {
    paletteResults.appendChild(buildPaletteRow("Overall vibe", combinedPalette));
  }
}

function buildPaletteRow(label, hexColors) {
  const row = document.createElement("div");
  row.className = "palette-row";

  const labelEl = document.createElement("div");
  labelEl.className = "palette-row-label";
  labelEl.textContent = label;
  row.appendChild(labelEl);

  hexColors.forEach((hex) => {
    const swatch = document.createElement("div");
    swatch.className = "swatch";

    const circle = document.createElement("div");
    circle.className = "swatch-circle";
    circle.style.backgroundColor = hex;

    const hexLabel = document.createElement("div");
    hexLabel.className = "swatch-hex";
    hexLabel.textContent = hex;

    swatch.appendChild(circle);
    swatch.appendChild(hexLabel);
    row.appendChild(swatch);
  });

  return row;
}