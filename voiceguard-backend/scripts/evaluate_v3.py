"""
VoiceGuard V3 — read-only evaluation
====================================
Loads the saved best V3 checkpoint and evaluates on:
  1. data/spectrograms/v3/test.npz
  2. Existing CD-ADD OpenVoice samples (from output/cdadd_v2_openvoice_baseline.csv)
  3. Existing CD-ADD VALL-E samples (from output/cdadd_v2_valle_baseline.csv)

Does NOT train, modify preprocessing, or overwrite existing model/result files.

Usage:
    python scripts/evaluate_v3.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "voiceguard_model_v3_best.h5"
TEST_NPZ = BASE_DIR / "data" / "spectrograms" / "v3" / "test.npz"
OUTPUT_DIR = BASE_DIR / "output"

OPENVOICE_BASELINE_CSV = OUTPUT_DIR / "cdadd_v2_openvoice_baseline.csv"
VALLE_BASELINE_CSV = OUTPUT_DIR / "cdadd_v2_valle_baseline.csv"
OPENVOICE_OUTPUT_CSV = OUTPUT_DIR / "cdadd_v3_openvoice.csv"
VALLE_OUTPUT_CSV = OUTPUT_DIR / "cdadd_v3_valle.csv"
REPORT_PATH = OUTPUT_DIR / "v3_evaluation_report.txt"

DATASET_ID = "SpeechAntiSpoofingBenchmarks/CD-ADD"
SPLIT = "test"
THRESHOLD = 0.5

sys.path.insert(0, str(BASE_DIR / "scripts"))
from audio_pipeline import process_audio  # noqa: E402


def load_sample_ids(csv_path: Path) -> list[str]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Baseline CSV not found: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row["sample_id"] for row in reader]


def evaluate_test_npz(model: tf.keras.Model) -> dict:
    data = np.load(TEST_NPZ)
    X_test, y_test = data["X"], data["y"]
    y_prob = model.predict(X_test, verbose=0)
    y_pred = np.argmax(y_prob, axis=1)

    acc = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average="binary", pos_label=1, zero_division=0)
    spoof_recall = recall_score(y_test, y_pred, average="binary", pos_label=1, zero_division=0)
    f1 = f1_score(y_test, y_pred, average="binary", pos_label=1, zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])

    return {
        "name": "V3 test.npz",
        "samples": len(y_test),
        "accuracy": acc,
        "precision": precision,
        "spoof_recall": spoof_recall,
        "f1": f1,
        "confusion_matrix": cm,
    }


def predict_audio_bytes(audio_bytes: bytes, model: tf.keras.Model) -> tuple[str, float, float]:
    spec = process_audio(audio_bytes, denoise=True, pre_emphasis=True, trim=True)
    if spec is None:
        raise ValueError("Audio processing failed")

    inp = spec[np.newaxis, ..., np.newaxis]
    probs = model.predict(inp, verbose=0)[0]
    bonafide_prob = float(probs[0])
    spoof_prob = float(probs[1])
    predicted = "AI GENERATED" if spoof_prob >= THRESHOLD else "HUMAN VOICE"
    return predicted, bonafide_prob, spoof_prob


def row_sample_id(row: dict) -> str:
    notes = json.loads(row["notes"])
    return notes.get("utterance_id") or row["path"]


def collect_cdadd_rows(sample_ids: list[str]) -> list[dict]:
    from datasets import Audio, load_dataset

    wanted = set(sample_ids)
    found: dict[str, dict] = {}

    stream = load_dataset(DATASET_ID, split=SPLIT, streaming=True)
    stream = stream.cast_column("audio", Audio(decode=False))

    for row in stream:
        sid = row_sample_id(row)
        if sid in wanted and sid not in found:
            found[sid] = row
            if len(found) == len(wanted):
                break

    missing = [sid for sid in sample_ids if sid not in found]
    if missing:
        raise RuntimeError(
            f"Could not locate {len(missing)} CD-ADD sample(s) via streaming. "
            f"First missing: {missing[0]}"
        )

    return [found[sid] for sid in sample_ids]


def compute_cdadd_metrics(results: list[dict]) -> dict:
    y_true = [1 if r["ground_truth"] == "spoof" else 0 for r in results]
    y_pred = [1 if r["predicted_class"] == "AI GENERATED" else 0 for r in results]

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    total = len(results)
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


def evaluate_cdadd_subset(
    model: tf.keras.Model,
    baseline_csv: Path,
    output_csv: Path,
    label: str,
) -> dict:
    sample_ids = load_sample_ids(baseline_csv)
    print(f"\n[->] CD-ADD {label}: streaming {len(sample_ids)} existing samples...")
    rows = collect_cdadd_rows(sample_ids)

    results: list[dict] = []
    for i, row in enumerate(rows, start=1):
        notes = json.loads(row["notes"])
        audio_bytes = row["audio"]["bytes"]
        if not audio_bytes:
            raise ValueError(f"Empty audio for sample {row_sample_id(row)}")

        ground_truth = "spoof" if int(row["label"]) == 1 else "bonafide"
        predicted, bonafide_prob, spoof_prob = predict_audio_bytes(audio_bytes, model)
        correct = (
            (ground_truth == "spoof" and predicted == "AI GENERATED")
            or (ground_truth == "bonafide" and predicted == "HUMAN VOICE")
        )

        results.append(
            {
                "sample_id": row_sample_id(row),
                "tts_system": notes.get("system", ""),
                "ground_truth": ground_truth,
                "predicted_class": predicted,
                "bonafide_probability": f"{bonafide_prob:.6f}",
                "spoof_probability": f"{spoof_prob:.6f}",
                "correct": "correct" if correct else "incorrect",
            }
        )

        if i % 10 == 0:
            print(f"     processed {i}/{len(rows)}")

    metrics = compute_cdadd_metrics(results)
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
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    return {
        "name": f"CD-ADD {label}",
        "samples": len(results),
        "baseline_csv": str(baseline_csv),
        "output_csv": str(output_csv),
        **metrics,
    }


def format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def render_report(test_metrics: dict, openvoice_metrics: dict, valle_metrics: dict) -> str:
    lines = [
        "=" * 60,
        "VoiceGuard V3 — read-only evaluation",
        f"Model: {MODEL_PATH}",
        "=" * 60,
        "",
        f"=== {test_metrics['name']} ===",
        f"Samples         : {test_metrics['samples']}",
        f"Accuracy        : {format_pct(test_metrics['accuracy'])}",
        f"Precision       : {format_pct(test_metrics['precision'])}  (spoof=positive)",
        f"Spoof recall    : {format_pct(test_metrics['spoof_recall'])}",
        f"F1              : {format_pct(test_metrics['f1'])}",
        "Confusion matrix: rows=actual [bonafide, spoof], cols=pred [bonafide, spoof]",
        f"                  {test_metrics['confusion_matrix'].tolist()}",
        "",
    ]

    for metrics in (openvoice_metrics, valle_metrics):
        cm = metrics["confusion_matrix"]
        lines.extend(
            [
                f"=== {metrics['name']} ===",
                f"Samples evaluated : {metrics['samples']}",
                f"Baseline CSV      : {metrics['baseline_csv']}",
                f"Output CSV        : {metrics['output_csv']}",
                f"Accuracy          : {format_pct(metrics['accuracy'])}",
                f"Spoof recall      : {format_pct(metrics['spoof_recall'])}",
                f"Bonafide recall   : {format_pct(metrics['bonafide_recall'])}",
                f"False positive    : {format_pct(metrics['false_positive_rate'])}",
                f"False negative    : {format_pct(metrics['false_negative_rate'])}",
                "Confusion matrix  : rows=actual [bonafide, spoof], cols=pred [bonafide, spoof]",
                f"                  {cm.tolist()}",
                f"                  TP={metrics['tp']} TN={metrics['tn']} FP={metrics['fp']} FN={metrics['fn']}",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> int:
    if not MODEL_PATH.exists():
        print(f"[!] Best V3 checkpoint not found: {MODEL_PATH}")
        return 1
    if not TEST_NPZ.exists():
        print(f"[!] Test NPZ not found: {TEST_NPZ}")
        return 1

    print(f"[OK] Found checkpoint: {MODEL_PATH}")
    print(f"     Size: {MODEL_PATH.stat().st_size:,} bytes")
    print(f"     Modified: {MODEL_PATH.stat().st_mtime}")

    print(f"\n[->] Loading model (read-only): {MODEL_PATH.name}")
    model = tf.keras.models.load_model(str(MODEL_PATH))

    print(f"\n[->] Evaluating {TEST_NPZ.relative_to(BASE_DIR)}...")
    test_metrics = evaluate_test_npz(model)
    print(f"[OK] {test_metrics['name']}: accuracy={format_pct(test_metrics['accuracy'])}")

    openvoice_metrics = evaluate_cdadd_subset(
        model,
        OPENVOICE_BASELINE_CSV,
        OPENVOICE_OUTPUT_CSV,
        "OpenVoice / LibriTTS",
    )
    valle_metrics = evaluate_cdadd_subset(
        model,
        VALLE_BASELINE_CSV,
        VALLE_OUTPUT_CSV,
        "VALL-E / LibriTTS",
    )

    report = render_report(test_metrics, openvoice_metrics, valle_metrics)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print("\n" + report)
    print(f"[OK] Report saved -> {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
