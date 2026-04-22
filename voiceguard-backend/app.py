"""
VoiceGuard — FastAPI Backend
Endpoint: POST /analyze
Accepts an audio file, runs the full audio pipeline + CNN inference,
returns a JSON verdict.

Run: python run.py
API docs: http://localhost:8000/docs
"""

import sys
import numpy as np
import tensorflow as tf
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our audio pipeline
sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from audio_pipeline import process_audio, load_audio, SAMPLE_RATE, DURATION

# ── Config ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "voiceguard_model.h5"

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".flac"}
ALLOWED_TYPES = {
    "audio/wav", "audio/wave", "audio/x-wav",
    "audio/mpeg", "audio/mp3",
    "audio/flac", "audio/x-flac",
    "application/octet-stream",
}

# ── App setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="VoiceGuard API",
    description="Deepfake audio detection via mel spectrogram CNN inference",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None

@app.on_event("startup")
def load_model():
    global model
    if not MODEL_PATH.exists():
        print(f"[!] Model not found at {MODEL_PATH}")
        print("    Run: python scripts/train.py")
        return
    print(f"[→] Loading model from {MODEL_PATH}...")
    model = tf.keras.models.load_model(str(MODEL_PATH))
    print("[✓] Model loaded and ready")


# ── Response schema ────────────────────────────────────────────────────────────
class AnalysisResult(BaseModel):
    verdict: str
    fake_percent: int
    real_percent: int
    confidence: int
    sample_rate: str
    duration: str


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "service": "VoiceGuard API",
        "status": "running",
        "model_loaded": model is not None,
    }


@app.get("/health")
def health():
    return {"status": "ok", "model_ready": model is not None}


@app.post("/analyze", response_model=AnalysisResult)
async def analyze_audio(file: UploadFile = File(...)):
    # Validate
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS and file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415,
            detail=f"Unsupported type. Use .wav, .mp3, or .flac")

    if model is None:
        raise HTTPException(status_code=503,
            detail="Model not loaded. Run python scripts/train.py first.")

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty file.")

    # Get duration + sample rate for display
    try:
        y_raw, sr = load_audio(audio_bytes)
        secs = len(y_raw) / sr
        duration_str  = f"{int(secs//60):02d}:{int(secs%60):02d}"
        samplerate_str = f"{sr/1000:.1f} kHz"
    except Exception:
        duration_str, samplerate_str = "00:00", "-- kHz"

    # Run full audio pipeline
    spec = process_audio(audio_bytes, denoise=True, pre_emphasis=True, trim=True)
    if spec is None:
        raise HTTPException(status_code=422,
            detail="Audio processing failed. File may be too short or corrupt.")

    # CNN inference — shape: (1, 128, 128, 1)
    inp   = spec[np.newaxis, ..., np.newaxis]
    probs = model.predict(inp, verbose=0)[0]   # [real_prob, fake_prob]

    real_prob    = float(probs[0])
    fake_prob    = float(probs[1])
    fake_percent = int(round(fake_prob * 100))
    real_percent = 100 - fake_percent
    confidence   = max(fake_percent, real_percent)
    verdict      = "AI GENERATED" if fake_prob >= 0.5 else "HUMAN VOICE"

    return AnalysisResult(
        verdict=verdict,
        fake_percent=fake_percent,
        real_percent=real_percent,
        confidence=confidence,
        sample_rate=samplerate_str,
        duration=duration_str,
    )
