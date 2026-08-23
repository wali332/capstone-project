"""
VoiceGuard — Batch Preprocessing Script
Runs audio files from ASVspoof split CSVs through the full processing
pipeline and saves spectrograms as compressed numpy archives per split.

Run:
  python scripts/preprocess.py               # full preprocessing (all splits)
  python scripts/preprocess.py --smoke-test  # 5 samples per split + verify
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from tqdm import tqdm
from audio_pipeline import process_audio

BASE_DIR = Path(__file__).resolve().parent.parent

SPLITS = {
    "train": BASE_DIR / "data" / "splits" / "train.csv",
    "validation": BASE_DIR / "data" / "splits" / "validation.csv",
    "test": BASE_DIR / "data" / "splits" / "test.csv",
}

OUTPUT_DIR = BASE_DIR / "data" / "spectrograms"
SMOKE_OUTPUT_DIR = OUTPUT_DIR / "smoke"
SMOKE_SAMPLES = 5

LABEL_MAP = {"bonafide": 0, "spoof": 1}


def load_split_rows(csv_path: Path, limit: int | None = None) -> list[dict]:
    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if limit is not None:
        rows = rows[:limit]
    return rows


def process_split(rows: list[dict], desc: str):
    X, y, ids, attacks, skipped = [], [], [], [], 0

    for row in tqdm(rows, desc=desc):
        audio_path = Path(row["audio_path"])
        label_str = row["label"].lower()

        if not audio_path.exists():
            skipped += 1
            continue

        if label_str not in LABEL_MAP:
            skipped += 1
            continue

        spec = process_audio(audio_path, denoise=True, pre_emphasis=True, trim=True)
        if spec is not None:
            X.append(spec)
            y.append(LABEL_MAP[label_str])
            ids.append(row["audio_id"])
            attacks.append(row.get("attack", ""))
        else:
            skipped += 1

    if skipped:
        print(f"  [!] Skipped {skipped} files (missing / corrupt / unknown label)")

    if not X:
        return None

    X_arr = np.array(X, dtype=np.float32)[..., np.newaxis]
    y_arr = np.array(y, dtype=np.int32)
    ids_arr = np.array(ids)
    attacks_arr = np.array(attacks)
    return X_arr, y_arr, ids_arr, attacks_arr


def save_split(output_path: Path, X, y, ids, attacks):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, X=X, y=y, ids=ids, attacks=attacks)


def verify_smoke_outputs(output_dir: Path, split_names: list[str]) -> bool:
    """Verify smoke-test outputs and cross-split ID overlap."""
    print("\n" + "=" * 55)
    print("  Smoke-test verification")
    print("=" * 55)

    all_ok = True
    all_ids = {}

    for name in split_names:
        path = output_dir / f"{name}.npz"
        print(f"\n[{name}] {path}")

        if not path.exists():
            print("  [FAIL] File not found")
            all_ok = False
            continue

        data = np.load(path)
        X, y, ids = data["X"], data["y"], data["ids"]

        shape_ok = X.ndim == 4 and X.shape[1:] == (128, 128, 1)
        dtype_ok = X.dtype == np.float32 and y.dtype == np.int32

        vmin, vmax = float(X.min()), float(X.max())
        range_ok = vmin >= 0.0 and vmax <= 1.0

        unique_labels = set(y.tolist())
        labels_ok = unique_labels.issubset({0, 1})
        bonafide = int((y == 0).sum())
        spoof = int((y == 1).sum())

        ids_ok = len(ids) == len(y) == len(X)

        checks = [
            ("shape", f"{X.shape}", shape_ok),
            ("dtype", f"X={X.dtype}, y={y.dtype}", dtype_ok),
            ("value range", f"[{vmin:.4f}, {vmax:.4f}]", range_ok),
            (
                "labels",
                f"bonafide={bonafide}, spoof={spoof}, unique={unique_labels}",
                labels_ok,
            ),
            ("IDs", f"{len(ids)} ids, aligned={ids_ok}", ids_ok),
        ]

        all_ids[name] = set(ids.tolist())

        for check_name, detail, ok in checks:
            status = "OK" if ok else "FAIL"
            print(f"  [{status}] {check_name}: {detail}")
            if not ok:
                all_ok = False

    print("\n[overlap]")
    for a, b in [("train", "validation"), ("train", "test"), ("validation", "test")]:
        if a in all_ids and b in all_ids:
            overlap = all_ids[a] & all_ids[b]
            ok = len(overlap) == 0
            status = "OK" if ok else "FAIL"
            print(f"  [{status}] {a} & {b}: {len(overlap)} shared ids")
            if not ok:
                all_ok = False

    if all_ok:
        print("\n[OK] All smoke checks passed")
    else:
        print("\n[!] Some smoke checks failed")

    return all_ok


def run_preprocessing(output_dir: Path, limit: int | None = None):
    print(f"\n    Pipeline: trim -> denoise -> pre-emphasis -> normalize -> mel spec")
    print(f"    Output  : {output_dir}")

    for name, csv_path in SPLITS.items():
        if not csv_path.exists():
            print(f"\n[!] Split CSV not found: {csv_path}")
            return False

        rows = load_split_rows(csv_path, limit=limit)
        print(f"\n[->] Processing {name}: {len(rows)} samples from {csv_path.name}")

        result = process_split(rows, desc=name)
        if result is None:
            print(f"  [!] No samples processed for {name}")
            return False

        X, y, ids, attacks = result
        out_path = output_dir / f"{name}.npz"
        save_split(out_path, X, y, ids, attacks)

        print(f"[OK] Saved {len(X)} spectrograms -> {out_path}")
        print(f"    Shape : X={X.shape}, y={y.shape}")
        print(f"    Bonafide (0): {(y == 0).sum()}, Spoof (1): {(y == 1).sum()}")

    return True


def main():
    parser = argparse.ArgumentParser(description="VoiceGuard mel spectrogram preprocessing")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help=f"Process only {SMOKE_SAMPLES} samples per split and verify outputs",
    )
    args = parser.parse_args()

    smoke = args.smoke_test
    limit = SMOKE_SAMPLES if smoke else None
    output_dir = SMOKE_OUTPUT_DIR if smoke else OUTPUT_DIR

    print("=" * 55)
    print("  VoiceGuard - Mel Spectrogram Preprocessing")
    if smoke:
        print(f"  Mode: smoke-test ({SMOKE_SAMPLES} samples per split)")
    print("=" * 55)

    ok = run_preprocessing(output_dir, limit=limit)
    if not ok:
        return 1

    if smoke:
        verify_ok = verify_smoke_outputs(output_dir, list(SPLITS.keys()))
        return 0 if verify_ok else 1

    print(f"\n[OK] Done! Run next: python scripts/train.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
