# VoiceGuard — Complete Setup Guide (Windows)

This guide takes you from zero to a fully working deepfake audio detector.
Follow each phase in order. Do not skip steps.

---

## Folder structure (what you'll end up with)

```
voiceguard/
├── voiceguard-backend/        ← Python backend (this folder)
│   ├── app.py                 ← FastAPI server
│   ├── run.py                 ← Server entry point
│   ├── requirements.txt
│   ├── start_server.bat       ← Double-click to start server
│   ├── models/
│   │   └── voiceguard_model.h5   ← Trained CNN (created in Phase 2)
│   ├── data/
│   │   ├── raw/               ← Downloaded dataset ZIP
│   │   ├── processed/
│   │   │   ├── real/          ← Organised real audio
│   │   │   └── fake/          ← Organised fake audio
│   │   └── spectrograms.npz   ← Preprocessed training data
│   └── scripts/
│       ├── download_dataset.py
│       ├── preprocess.py
│       └── train.py
│
└── capstone-project-main/     ← Your existing React frontend
    └── src/components/
        └── LiveDemo.jsx       ← Replace with the new version
```

---

## Phase 1 — Python environment setup

Open **Command Prompt** or **PowerShell** as Administrator.

```bat
:: Check Python version (need 3.10 or 3.11)
python --version

:: Create a virtual environment in the backend folder
cd voiceguard-backend
python -m venv venv

:: Activate it
venv\Scripts\activate

:: You should see (venv) at the start of your prompt now

:: Install all dependencies
pip install -r requirements.txt
```

This will take 3–5 minutes (TensorFlow is large).

---

## Phase 2 — Download the dataset

Make sure your venv is still active (`venv\Scripts\activate`).

```bat
python scripts/download_dataset.py
```

This downloads the **FOR-norm dataset** (~600MB) from Zenodo — a public,
labelled dataset of real and AI-generated speech. It then organises all
files into `data/processed/real/` and `data/processed/fake/`.

Expected output:
```
[✓] Downloaded to data/raw/for-norm.zip
[✓] Extracted to data/raw/for-norm
[✓] Dataset organised:
    Real files : ~5000
    Fake files : ~5000
    Total      : ~10000
```

---

## Phase 3 — Preprocess (audio → spectrograms)

```bat
python scripts/preprocess.py
```

Converts every audio file into a 128×128 mel spectrogram and saves them
all into a single compressed file (`data/spectrograms.npz`).

Takes ~10–20 minutes depending on your CPU. You'll see a progress bar.

Expected output:
```
[✓] Saved ~8000 spectrograms → data/spectrograms.npz
    Shape: X=(8000, 128, 128, 1), y=(8000,)
```

---

## Phase 4 — Train the CNN model

```bat
python scripts/train.py
```

Trains the CNN for up to 30 epochs with early stopping.
On a modern laptop CPU this takes **30–90 minutes**.
On a GPU it takes ~5 minutes.

Expected output:
```
Epoch 1/30 - accuracy: 0.62 - val_accuracy: 0.71
Epoch 2/30 - accuracy: 0.74 - val_accuracy: 0.79
...
[✓] Final validation accuracy: ~88-92%
[✓] Model saved → models/voiceguard_model.h5
[✓] Training plot saved → models/training_history.png
```

The model file (`voiceguard_model.h5`) is what the API loads.

---

## Phase 5 — Start the FastAPI server

```bat
:: Make sure venv is active
venv\Scripts\activate

:: Start the server
python run.py
```

Or just double-click `start_server.bat`.

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
[→] Loading model from models/voiceguard_model.h5...
[✓] Model loaded and ready
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Test it: open http://localhost:8000 in your browser.
API docs: http://localhost:8000/docs

---

## Phase 6 — Wire up the frontend

1. Copy the new `LiveDemo.jsx` from this folder into your React project:

```bat
copy LiveDemo.jsx ..\capstone-project-main\src\components\LiveDemo.jsx
```

2. Start your React dev server (in a separate terminal):

```bat
cd ..\capstone-project-main
npm install
npm run dev
```

3. Open http://localhost:5173 in your browser.

4. Upload a `.wav`, `.mp3`, or `.flac` file — you'll get a real verdict
   from your trained CNN model.

---

## Troubleshooting

**"Cannot reach backend" error in the browser:**
- Make sure `python run.py` is running in another terminal
- Check http://localhost:8000/health returns `{"status":"ok"}`

**"Model not loaded" error:**
- Run `python scripts/train.py` and wait for it to finish
- Check that `models/voiceguard_model.h5` exists

**Download fails / slow:**
- The Zenodo server can be slow. Try again or use a VPN.
- Alternatively, download manually from: https://zenodo.org/record/4319978
  and place the ZIP at `data/raw/for-norm.zip`

**pip install fails on TensorFlow:**
- Make sure you're using Python 3.10 or 3.11 (not 3.12+)
- Try: `pip install tensorflow-cpu` instead if you have no GPU

**CORS error in browser console:**
- The API already allows all origins in development
- Make sure you're accessing React at localhost:5173 or localhost:3000

---

## API reference

### POST /analyze

Upload an audio file, get a verdict back.

**Request:** `multipart/form-data` with field `file` (.wav / .mp3 / .flac)

**Response:**
```json
{
  "verdict": "AI GENERATED",
  "fake_percent": 87,
  "real_percent": 13,
  "confidence": 87,
  "sample_rate": "22.1 kHz",
  "duration": "00:03"
}
```

### GET /health
```json
{ "status": "ok", "model_ready": true }
```
