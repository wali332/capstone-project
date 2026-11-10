"""
VoiceGuard V2 — CD-ADD external TTS evaluation
================================================
Evaluates the existing V2 model on a small CD-ADD subset without training
or changing preprocessing / thresholds.

CD-ADD Hugging Face schema (SpeechAntiSpoofingBenchmarks/CD-ADD):
  - path   : str          — unique source-relative file path
  - audio  : Audio        — 16 kHz mono (FLAC bytes when decode=False)
  - label  : ClassLabel   — 0 = bonafide, 1 = spoof
  - notes  : str (JSON)   — utterance_id, source, system, speaker_id, transcript
      source : "libritts" | "ted"
      system : "real" | "openvoice" | "valle" | "whisperSpeech" | "yourTTS" | "seamless"

Requires (not in requirements.txt): pip install datasets

Usage:
    python scripts/evaluate_cdadd.py
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.metrics import confusion_matrix

# ── Project paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "voiceguard_model_v2.h5"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_CSV = OUTPUT_DIR / "cdadd_v2_openvoice_baseline.csv"

sys.path.insert(0, str(BASE_DIR / "scripts"))
from audio_pipeline import process_audio  # noqa: E402

# ── Eval config (first test) ───────────────────────────────────────────────────
DATASET_ID = "SpeechAntiSpoofingBenchmarks/CD-ADD"
SPLIT = "test"
SOURCE_FILTER = "libritts"
SPOOF_SYSTEM = "openvoice"
BONAFIDE_SYSTEM = "real"
N_BONAFIDE = 50
N_SPOOF = 50
THRESHOLD = 0.5  # same as app.py

REQUIRED_FIELDS = {"path", "audio", "label", "notes"}
REQUIRED_NOTE_KEYS = {"utterance_id", "source", "system", "speaker_id", "transcript"}
LABEL_NAMES = {0: "bonafide", 1: "spoof"}


def verify_schema(example: dict) -> None:
    """Abort if the live CD-ADD row does not match the documented schema."""
    missing = REQUIRED_FIELDS - set(example.keys())
    if missing:
        raise RuntimeError(
            f"CD-ADD schema mismatch: missing top-level fields {sorted(missing)}. "
            f"Found: {sorted(example.keys())}"
        )

    notes = json.loads(example["notes"])
    missing_notes = REQUIRED_NOTE_KEYS - set(notes.keys())
    if missing_notes:
        raise RuntimeError(
            f"CD-ADD notes JSON mismatch: missing keys {sorted(missing_notes)}. "
            f"Found: {sorted(notes.keys())}"
        )

    audio = example["audio"]
    if not isinstance(audio, dict) or "bytes" not in audio:
        raise RuntimeError(
            "CD-ADD audio field must be a dict with 'bytes' when decode=False. "
            f"Got: {type(audio).__name__} keys={list(audio.keys()) if isinstance(audio, dict) else 'n/a'}"
        )


def parse_notes(notes_raw: str) -> dict:
    return json.loads(notes_raw)


def label_to_name(label) -> str:
    if isinstance(label, str):
        return label
    return LABEL_NAMES[int(label)]


def predict(audio_bytes: bytes, model: tf.keras.Model) -> tuple[str, float, float]:
    """Mirror app.py /analyze inference exactly."""
    spec = process_audio(audio_bytes, denoise=True, pre_emphasis=True, trim=True)
    if spec is None:
        raise ValueError("Audio processing failed")

    inp = spec[np.newaxis, ..., np.newaxis]
    probs = model.predict(inp, verbose=0)[0]  # [real_prob, fake_prob]

    bonafide_prob = float(probs[0])
    spoof_prob = float(probs[1])
    predicted = "AI GENERATED" if spoof_prob >= THRESHOLD else "HUMAN VOICE"
    return predicted, bonafide_prob, spoof_prob


def collect_subset():
    from datasets import Audio, load_dataset

    stream = load_dataset(DATASET_ID, split=SPLIT, streaming=True)
    stream = stream.cast_column("audio", Audio(decode=False))

    iterator = iter(stream)
    try:
        first = next(iterator)
    except StopIteration:
        raise RuntimeError("CD-ADD test split is empty")

    verify_schema(first)
    print("[OK] CD-ADD schema verified:")
    print("     fields: path, audio, label, notes")
    print("     notes:  utterance_id, source, system, speaker_id, transcript")

    bonafide_rows = []
    spoof_rows = []

    def consider(row: dict) -> None:
        notes = parse_notes(row["notes"])
        if notes.get("source") != SOURCE_FILTER:
            return

        system = notes.get("system")
        label_name = label_to_name(row["label"])

        if system == BONAFIDE_SYSTEM and label_name == "bonafide" and len(bonafide_rows) < N_BONAFIDE:
            bonafide_rows.append(row)
        elif system == SPOOF_SYSTEM and label_name == "spoof" and len(spoof_rows) < N_SPOOF:
            spoof_rows.append(row)

    consider(first)

    for row in iterator:
        if len(bonafide_rows) >= N_BONAFIDE and len(spoof_rows) >= N_SPOOF:
            break
        consider(row)

    if len(bonafide_rows) < N_BONAFIDE or len(spoof_rows) < N_SPOOF:
        raise RuntimeError(
            f"Could not collect enough samples "
            f"(bonafide={len(bonafide_rows)}/{N_BONAFIDE}, "
            f"spoof={len(spoof_rows)}/{N_SPOOF}). "
            f"Check filters source={SOURCE_FILTER!r}, "
            f"system in ({BONAFIDE_SYSTEM!r}, {SPOOF_SYSTEM!r})."
        )

    return bonafide_rows + spoof_rows


def compute_metrics(rows: list[dict]) -> dict:
    y_true = [1 if r["ground_truth"] == "spoof" else 0 for r in rows]
    y_pred = [1 if r["predicted_class"] == "AI GENERATED" else 0 for r in rows]

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    total = len(rows)
    accuracy = (tp + tn) / total if total else 0.0
    spoof_recall = tp / (tp + fn) if (tp + fn) else 0.0
    bonafide_recall = tn / (tn + fp) if (tn + fp) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    fnr = fn / (fn + tp) if (fn + tp) else 0.0
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

    return {
        "accuracy": accuracy,
        "spoof_recall": spoof_recall,
        "bonafide_recall": bonafide_recall,
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "confusion_matrix": cm,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def main() -> int:
    if not MODEL_PATH.exists():
        print(f"[!] Model not found: {MODEL_PATH}")
        return 1

    print(f"[->] Loading model: {MODEL_PATH.name}")
    model = tf.keras.models.load_model(str(MODEL_PATH))

    print(
        f"[->] Streaming CD-ADD subset: source={SOURCE_FILTER}, "
        f"system={SPOOF_SYSTEM}, {N_BONAFIDE} bonafide + {N_SPOOF} spoof"
    )
    subset = collect_subset()
    print(f"[OK] Collected {len(subset)} samples (streaming; full dataset not downloaded)")

    results: list[dict] = []

    for i, row in enumerate(subset, start=1):
        notes = parse_notes(row["notes"])
        audio_bytes = row["audio"]["bytes"]
        if not audio_bytes:
            print(f"[!] Skipping empty audio: {row['path']}")
            continue

        ground_truth = label_to_name(row["label"])
        sample_id = notes.get("utterance_id") or row["path"]
        system = notes.get("system", "")

        try:
            predicted, bonafide_prob, spoof_prob = predict(audio_bytes, model)
        except Exception as exc:
            print(f"[!] Failed on {sample_id}: {exc}")
            continue

        correct = (
            (ground_truth == "spoof" and predicted == "AI GENERATED")
            or (ground_truth == "bonafide" and predicted == "HUMAN VOICE")
        )

        results.append(
            {
                "sample_id": sample_id,
                "tts_system": system,
                "ground_truth": ground_truth,
                "predicted_class": predicted,
                "bonafide_probability": f"{bonafide_prob:.6f}",
                "spoof_probability": f"{spoof_prob:.6f}",
                "correct": "correct" if correct else "incorrect",
            }
        )

        if i % 10 == 0:
            print(f"     processed {i}/{len(subset)}")

    if not results:
        print("[!] No samples evaluated successfully")
        return 1

    metrics = compute_metrics(results)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id",
        "tts_system",
        "ground_truth",
        "predicted_class",
        "bonafide_probability",
        "spoof_probability",
        "correct",
    ]
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    cm = metrics["confusion_matrix"]
    print("\n=== VoiceGuard V2 — CD-ADD OpenVoice / LibriTTS baseline ===")
    print(f"Samples evaluated : {len(results)}")
    print(f"Output CSV        : {OUTPUT_CSV}")
    print(f"Accuracy          : {metrics['accuracy']:.1%}")
    print(f"Spoof recall      : {metrics['spoof_recall']:.1%}  (detection rate)")
    print(f"Bonafide recall   : {metrics['bonafide_recall']:.1%}")
    print(f"False positive    : {metrics['false_positive_rate']:.1%}  (bonafide -> spoof)")
    print(f"False negative    : {metrics['false_negative_rate']:.1%}  (spoof -> bonafide)")
    print("Confusion matrix  : rows=actual [bonafide, spoof], cols=predicted [bonafide, spoof]")
    print(f"                    {cm.tolist()}")
    print(f"                    TP={metrics['tp']} TN={metrics['tn']} FP={metrics['fp']} FN={metrics['fn']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
