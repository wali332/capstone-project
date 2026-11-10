"""
VoiceGuard V3 — Batch Preprocessing
===================================
Runs V3 split CSVs through the same pipeline as V2 preprocess.py.
Does NOT modify or overwrite V2 NPZ files.

Run from project root:
    python scripts/preprocess_v3.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from tqdm import tqdm
from audio_pipeline import process_audio

BASE_DIR = Path(__file__).resolve().parent.parent

SPLITS = {
    "train": BASE_DIR / "data" / "v3_splits" / "train.csv",
    "validation": BASE_DIR / "data" / "v3_splits" / "validation.csv",
    "test": BASE_DIR / "data" / "v3_splits" / "test.csv",
}

OUTPUT_DIR = BASE_DIR / "data" / "spectrograms" / "v3"
LABEL_MAP = {"bonafide": 0, "spoof": 1}


def resolve_audio_path(audio_path: str) -> Path:
    p = Path(audio_path)
    if p.is_absolute():
        return p
    return BASE_DIR / p


def load_split_rows(csv_path: Path) -> list[dict]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def process_split(rows: list[dict], desc: str):
    X, y, ids, attacks, skipped = [], [], [], [], []
    skip_reasons = {"missing": 0, "bad_label": 0, "pipeline_fail": 0}

    for row in tqdm(rows, desc=desc):
        audio_path = resolve_audio_path(row["audio_path"])
        label_str = row["label"].lower()

        if not audio_path.exists():
            skipped.append((row["audio_id"], "missing", str(audio_path)))
            skip_reasons["missing"] += 1
            continue

        if label_str not in LABEL_MAP:
            skipped.append((row["audio_id"], "bad_label", label_str))
            skip_reasons["bad_label"] += 1
            continue

        spec = process_audio(audio_path, denoise=True, pre_emphasis=True, trim=True)
        if spec is None:
            skipped.append((row["audio_id"], "pipeline_fail", str(audio_path)))
            skip_reasons["pipeline_fail"] += 1
            continue

        X.append(spec)
        y.append(LABEL_MAP[label_str])
        ids.append(row["audio_id"])
        attacks.append(row.get("attack", ""))

    if skipped:
        print(f"  [!] Skipped {len(skipped)} files:")
        print(f"      missing={skip_reasons['missing']}, bad_label={skip_reasons['bad_label']}, pipeline_fail={skip_reasons['pipeline_fail']}")
        for item in skipped[:5]:
            print(f"        {item}")
        if len(skipped) > 5:
            print(f"        ... and {len(skipped) - 5} more")

    if not X:
        return None, skipped

    X_arr = np.array(X, dtype=np.float32)[..., np.newaxis]
    y_arr = np.array(y, dtype=np.int32)
    ids_arr = np.array(ids)
    attacks_arr = np.array(attacks)
    return (X_arr, y_arr, ids_arr, attacks_arr), skipped


def save_split(output_path: Path, X, y, ids, attacks):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, X=X, y=y, ids=ids, attacks=attacks)


def verify_outputs(output_dir: Path, all_skipped: dict) -> bool:
    print("\n" + "=" * 55)
    print("  V3 preprocessing verification")
    print("=" * 55)

    ok = True
    for name in SPLITS:
        path = output_dir / f"{name}.npz"
        print(f"\n[{name}] {path}")

        if not path.exists():
            print("  [FAIL] File not found")
            ok = False
            continue

        data = np.load(path)
        X, y = data["X"], data["y"]

        nan_count = int(np.isnan(X).sum())
        inf_count = int(np.isinf(X).sum())
        bonafide = int((y == 0).sum())
        spoof = int((y == 1).sum())
        skipped = all_skipped.get(name, [])

        checks = [
            ("X shape", str(X.shape), X.ndim == 4 and X.shape[1:] == (128, 128, 1)),
            ("y shape", str(y.shape), y.ndim == 1 and len(y) == len(X)),
            ("bonafide (0)", str(bonafide), bonafide > 0),
            ("spoof (1)", str(spoof), spoof > 0),
            ("failed files", str(len(skipped)), True),
            ("NaN values", str(nan_count), nan_count == 0),
            ("Inf values", str(inf_count), inf_count == 0),
        ]

        for check_name, detail, passed in checks:
            status = "OK" if passed else "FAIL"
            print(f"  [{status}] {check_name}: {detail}")
            if not passed:
                ok = False

    print("\n[output paths for V3 training]")
    for name in SPLITS:
        print(f"  {output_dir / f'{name}.npz'}")

    return ok


def main() -> int:
    print("=" * 55)
    print("  VoiceGuard V3 — Mel Spectrogram Preprocessing")
    print("=" * 55)
    print("  Pipeline: same as V2 (trim, denoise, pre-emphasis, 16kHz, 4s, 128x128 mel)")
    print(f"  Output  : {OUTPUT_DIR}")
    print("  Note    : V2 NPZ files are NOT modified")

    all_skipped = {}

    for name, csv_path in SPLITS.items():
        if not csv_path.exists():
            print(f"\n[!] Split CSV not found: {csv_path}")
            return 1

        rows = load_split_rows(csv_path)
        print(f"\n[->] Processing {name}: {len(rows)} samples from {csv_path.name}")

        result, skipped = process_split(rows, desc=name)
        all_skipped[name] = skipped

        if result is None:
            print(f"  [!] No samples processed for {name}")
            return 1

        X, y, ids, attacks = result
        out_path = OUTPUT_DIR / f"{name}.npz"
        save_split(out_path, X, y, ids, attacks)

        print(f"[OK] Saved {len(X)} spectrograms -> {out_path}")
        print(f"    X={X.shape}, y={y.shape}")
        print(f"    Bonafide (0): {(y == 0).sum()}, Spoof (1): {(y == 1).sum()}")

    if not verify_outputs(OUTPUT_DIR, all_skipped):
        return 1

    print("\n[OK] V3 preprocessing complete. Ready for V3 training when approved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
