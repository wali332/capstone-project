"""
VoiceGuard V3 — Metadata integration
=====================================
Builds a separate V3 dataset by combining existing ASVspoof bonafide/spoof
rows from balanced_metadata.csv with 400 MLAAD-tiny English spoof samples.

No physical audio file is duplicated. Each audio_path appears at most once.

Run from project root (voiceguard-backend/):
    python data/create_v3_metadata.py
"""

from __future__ import annotations

import csv
import random
import sys
from collections import Counter
from pathlib import Path

from sklearn.model_selection import train_test_split

# ── Paths (relative to voiceguard-backend root) ───────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
BALANCED_METADATA = BASE_DIR / "data" / "balanced_metadata.csv"
MLAAD_ROOT = BASE_DIR / "data" / "external" / "mlaad-tiny" / "fake" / "en"
OUTPUT_METADATA = BASE_DIR / "data" / "v3_metadata.csv"
OUTPUT_SPLITS_DIR = BASE_DIR / "data" / "v3_splits"

FIELDNAMES = ["audio_id", "audio_path", "label", "attack"]
SEED = 42

TARGET_BONAFIDE = 3800
TARGET_SPOOF = 3800
TARGET_TOTAL = 7600
ASVSPOOF_SPOOF = 3400
MLAAD_SPOOF = 400
MLAAD_PER_MODEL = 100

EXPECTED_TRAIN = 5320
EXPECTED_VAL = 1140
EXPECTED_TEST = 1140

MLAAD_MODELS = [
    ("Edge-TTS", "MLAAD_EDGE_TTS"),
    ("MeloTTS", "MLAAD_MELOTTS"),
    ("suno_bark", "MLAAD_SUNO_BARK"),
    ("DeepGram", "MLAAD_DEEPGRAM"),
]

ALLOWED_MLAAD_ATTACKS = {model for model, _ in MLAAD_MODELS}


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def resolve_audio_path(audio_path: str) -> Path:
    p = Path(audio_path)
    if p.is_absolute():
        return p.resolve()
    return (BASE_DIR / p).resolve()


def canonical_path(audio_path: str) -> str:
    return str(resolve_audio_path(audio_path))


def load_asvspoof_bonafide() -> list[dict]:
    balanced = read_csv(BALANCED_METADATA)
    bonafide = [r for r in balanced if r["label"] == "bonafide"]
    if len(bonafide) != TARGET_BONAFIDE:
        raise RuntimeError(f"Expected {TARGET_BONAFIDE} balanced bonafide rows, got {len(bonafide)}")
    return bonafide


def load_asvspoof_spoof_subset() -> list[dict]:
    balanced = read_csv(BALANCED_METADATA)
    spoof_pool = [r for r in balanced if r["label"] == "spoof"]
    if len(spoof_pool) != TARGET_SPOOF:
        raise RuntimeError(f"Expected {TARGET_SPOOF} balanced spoof rows, got {len(spoof_pool)}")

    rng = random.Random(SEED)
    return rng.sample(spoof_pool, ASVSPOOF_SPOOF)


def load_mlaad_spoof_rows() -> list[dict]:
    rows: list[dict] = []

    for model_dir_name, id_prefix in MLAAD_MODELS:
        model_dir = MLAAD_ROOT / model_dir_name
        if not model_dir.is_dir():
            raise RuntimeError(f"Missing MLAAD model directory: {model_dir}")

        wavs = sorted(model_dir.glob("*.wav"))
        if len(wavs) != MLAAD_PER_MODEL:
            raise RuntimeError(
                f"{model_dir_name}: expected {MLAAD_PER_MODEL} WAV files, got {len(wavs)}"
            )

        for i, wav in enumerate(wavs, start=1):
            rel_path = wav.relative_to(BASE_DIR).as_posix()
            rows.append(
                {
                    "audio_id": f"{id_prefix}_{i:04d}",
                    "audio_path": rel_path,
                    "label": "spoof",
                    "attack": model_dir_name,
                }
            )

    return rows


def build_v3_metadata() -> list[dict]:
    bonafide = load_asvspoof_bonafide()
    spoof_asv = load_asvspoof_spoof_subset()
    mlaad_spoof = load_mlaad_spoof_rows()

    v3_rows = bonafide + spoof_asv + mlaad_spoof

    rng = random.Random(SEED)
    rng.shuffle(v3_rows)
    return v3_rows


def split_v3_metadata(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    labels = [r["label"] for r in rows]

    train_rows, temp_rows = train_test_split(
        rows,
        test_size=0.30,
        random_state=SEED,
        stratify=labels,
    )
    val_rows, test_rows = train_test_split(
        temp_rows,
        test_size=0.50,
        random_state=SEED,
        stratify=[r["label"] for r in temp_rows],
    )
    return train_rows, val_rows, test_rows


def is_mlaad_row(row: dict) -> bool:
    return row["audio_id"].startswith("MLAAD_")


def count_mlaad(rows: list[dict]) -> int:
    return sum(1 for r in rows if is_mlaad_row(r))


def validate_v3_metadata(rows: list[dict]) -> bool:
    print("\n" + "=" * 55)
    print("  V3 metadata validation")
    print("=" * 55)

    ok = True

    def check(name: str, passed: bool, detail: str = "") -> None:
        nonlocal ok
        status = "OK" if passed else "FAIL"
        suffix = f" — {detail}" if detail else ""
        print(f"  [{status}] {name}{suffix}")
        if not passed:
            ok = False

    check("v3_metadata.csv will be written", True, str(OUTPUT_METADATA))
    check("Exactly 7,600 rows", len(rows) == TARGET_TOTAL, f"got {len(rows)}")

    labels = Counter(r["label"] for r in rows)
    check("Exactly 3,800 bonafide", labels["bonafide"] == TARGET_BONAFIDE, str(labels["bonafide"]))
    check("Exactly 3,800 spoof", labels["spoof"] == TARGET_SPOOF, str(labels["spoof"]))

    mlaad_rows = [r for r in rows if is_mlaad_row(r)]
    asvspoof_spoof_rows = [r for r in rows if r["label"] == "spoof" and not is_mlaad_row(r)]

    check("Exactly 400 MLAAD spoof rows", len(mlaad_rows) == MLAAD_SPOOF, str(len(mlaad_rows)))
    check(
        "Exactly 3,400 ASVspoof spoof rows",
        len(asvspoof_spoof_rows) == ASVSPOOF_SPOOF,
        str(len(asvspoof_spoof_rows)),
    )

    mlaad_attacks = Counter(r["attack"] for r in mlaad_rows)
    for model in sorted(ALLOWED_MLAAD_ATTACKS):
        check(
            f"Exactly 100 MLAAD samples for {model}",
            mlaad_attacks[model] == MLAAD_PER_MODEL,
            str(mlaad_attacks.get(model, 0)),
        )

    ids = [r["audio_id"] for r in rows]
    check("No duplicate audio_id values", len(ids) == len(set(ids)), f"{len(ids) - len(set(ids))} duplicates")

    canonical_paths = [canonical_path(r["audio_path"]) for r in rows]
    check(
        "No duplicated physical audio paths",
        len(canonical_paths) == len(set(canonical_paths)),
        f"{len(canonical_paths) - len(set(canonical_paths))} duplicates",
    )

    bonafide_paths = [canonical_path(r["audio_path"]) for r in rows if r["label"] == "bonafide"]
    check(
        "Exactly 3,800 unique bonafide physical files",
        len(set(bonafide_paths)) == TARGET_BONAFIDE,
        f"{len(set(bonafide_paths))} unique",
    )

    missing = [r["audio_id"] for r in rows if not resolve_audio_path(r["audio_path"]).exists()]
    check("Every audio_path exists", len(missing) == 0, f"{len(missing)} missing")

    extra_bonafide = [r for r in rows if r["audio_id"].startswith("ASV_BONAFIDE_EXTRA_")]
    check("No duplicated ASVspoof bonafide rows", len(extra_bonafide) == 0, str(len(extra_bonafide)))

    balanced = read_csv(BALANCED_METADATA)
    balanced_bonafide_ids = {r["audio_id"] for r in balanced if r["label"] == "bonafide"}
    v3_bal_bonafide = [r for r in rows if r["audio_id"] in balanced_bonafide_ids]
    check(
        "Existing ASVspoof bonafide rows preserved",
        len(v3_bal_bonafide) == TARGET_BONAFIDE,
        f"{len(v3_bal_bonafide)} found",
    )

    check("No MLAAD bonafide files", all(r["label"] == "spoof" for r in mlaad_rows))
    unexpected_mlaad = {
        r["attack"] for r in mlaad_rows if r["attack"] not in ALLOWED_MLAAD_ATTACKS
    }
    check("No other MLAAD models", len(unexpected_mlaad) == 0, str(unexpected_mlaad or "none"))

    return ok


def validate_splits(
    train_rows: list[dict],
    val_rows: list[dict],
    test_rows: list[dict],
) -> bool:
    print("\n" + "=" * 55)
    print("  V3 split validation")
    print("=" * 55)

    ok = True
    splits = {
        "train": train_rows,
        "validation": val_rows,
        "test": test_rows,
    }

    all_ids: set[str] = set()
    all_paths: set[str] = set()

    for name, data in splits.items():
        ids = {r["audio_id"] for r in data}
        paths = {canonical_path(r["audio_path"]) for r in data}
        id_overlap = all_ids & ids
        path_overlap = all_paths & paths
        all_ids.update(ids)
        all_paths.update(paths)

        labels = Counter(r["label"] for r in data)
        has_both = labels["bonafide"] > 0 and labels["spoof"] > 0

        expected_size = {
            "train": EXPECTED_TRAIN,
            "validation": EXPECTED_VAL,
            "test": EXPECTED_TEST,
        }[name]
        size_ok = len(data) == expected_size

        status = "OK" if not id_overlap and not path_overlap and has_both and size_ok else "FAIL"
        print(
            f"  [{status}] {name}: {len(data)} rows "
            f"(expected {expected_size}), bonafide={labels['bonafide']}, spoof={labels['spoof']}"
        )
        if id_overlap:
            print(f"         duplicate audio_id vs prior splits: {len(id_overlap)}")
            ok = False
        if path_overlap:
            print(f"         duplicate audio_path vs prior splits: {len(path_overlap)}")
            ok = False
        if not has_both:
            ok = False
        if not size_ok:
            ok = False

        mlaad_n = count_mlaad(data)
        mlaad_by_attack = Counter(r["attack"] for r in data if is_mlaad_row(r))
        print(f"         MLAAD spoof samples: {mlaad_n}")
        if mlaad_by_attack:
            print(f"         MLAAD by system: {dict(sorted(mlaad_by_attack.items()))}")

    check_no_path_overlap = len(all_paths) == len(all_ids)
    status = "OK" if check_no_path_overlap else "FAIL"
    print(f"  [{status}] No audio_path overlap between train/validation/test")
    if not check_no_path_overlap:
        ok = False

    return ok


def print_summary_table(
    rows: list[dict],
    train_rows: list[dict],
    val_rows: list[dict],
    test_rows: list[dict],
) -> None:
    print("\n" + "=" * 55)
    print("  V3 summary")
    print("=" * 55)
    print(f"  {'Split':<12} {'Total':>6} {'Bonafide':>9} {'Spoof':>7} {'MLAAD':>7}")
    print(f"  {'-'*12} {'-'*6} {'-'*9} {'-'*7} {'-'*7}")

    for name, data in [
        ("train", train_rows),
        ("validation", val_rows),
        ("test", test_rows),
        ("ALL", rows),
    ]:
        labels = Counter(r["label"] for r in data)
        mlaad_n = count_mlaad(data)
        print(
            f"  {name:<12} {len(data):>6} {labels['bonafide']:>9} "
            f"{labels['spoof']:>7} {mlaad_n:>7}"
        )

    print(f"\n  Output metadata : {OUTPUT_METADATA.relative_to(BASE_DIR)}")
    print(f"  Output splits   : {OUTPUT_SPLITS_DIR.relative_to(BASE_DIR)}/")


def main() -> int:
    print("=" * 55)
    print("  VoiceGuard V3 — Metadata creation")
    print("=" * 55)
    print(f"  Project root : {BASE_DIR}")

    if not BALANCED_METADATA.exists():
        print(f"[!] Missing {BALANCED_METADATA}")
        return 1
    if not MLAAD_ROOT.exists():
        print(f"[!] Missing MLAAD root: {MLAAD_ROOT}")
        print("    Run: python download_mlaad.py")
        return 1

    print("\n[->] Building V3 metadata...")
    v3_rows = build_v3_metadata()

    if not validate_v3_metadata(v3_rows):
        print("\n[!] Metadata validation failed — files not written")
        return 1

    write_csv(OUTPUT_METADATA, v3_rows)
    print(f"\n[OK] Saved {len(v3_rows)} rows -> {OUTPUT_METADATA.relative_to(BASE_DIR)}")

    print("\n[->] Creating V3 splits (70/15/15, stratified by label)...")
    train_rows, val_rows, test_rows = split_v3_metadata(v3_rows)

    write_csv(OUTPUT_SPLITS_DIR / "train.csv", train_rows)
    write_csv(OUTPUT_SPLITS_DIR / "validation.csv", val_rows)
    write_csv(OUTPUT_SPLITS_DIR / "test.csv", test_rows)

    if not validate_splits(train_rows, val_rows, test_rows):
        print("\n[!] Split validation failed")
        return 1

    print_summary_table(v3_rows, train_rows, val_rows, test_rows)
    print("\n[OK] V3 metadata pipeline complete. Ready for preprocessing when approved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
