"""
VoiceGuard V3 — MLAAD-tiny external spoof download
==================================================
Selectively downloads 4 English spoof folders (~400 WAV files) from
mueller91/MLAAD-tiny without fetching bonafide audio or the full repo.

Run from voiceguard-backend/:
    python download_mlaad.py

Requires: huggingface_hub  (pip install huggingface_hub)
"""

from pathlib import Path

from huggingface_hub import snapshot_download

BASE_DIR = Path(__file__).resolve().parent
LOCAL_DIR = BASE_DIR / "data" / "external" / "mlaad-tiny"

REPO_ID = "mueller91/MLAAD-tiny"
REVISION = "9143e5e"
ALLOW_PATTERNS = [
    "fake/en/Edge-TTS/*",
    "fake/en/MeloTTS/*",
    "fake/en/suno_bark/*",
    "fake/en/DeepGram/*",
]
EXPECTED_MODELS = ["Edge-TTS", "MeloTTS", "suno_bark", "DeepGram"]


def verify_download(root: Path) -> bool:
    """Confirm expected folder layout and ~400 spoof WAV files."""
    print("\n" + "=" * 55)
    print("  Download verification")
    print("=" * 55)

    ok = True
    total_wavs = 0

    for model in EXPECTED_MODELS:
        model_dir = root / "fake" / "en" / model
        meta = model_dir / "meta.csv"
        wavs = list(model_dir.glob("*.wav")) if model_dir.exists() else []

        meta_ok = meta.exists()
        wav_ok = len(wavs) >= 90  # expect ~100; allow small tolerance
        total_wavs += len(wavs)

        status = "OK" if meta_ok and wav_ok else "FAIL"
        print(f"  [{status}] fake/en/{model}/")
        print(f"         meta.csv : {'yes' if meta_ok else 'missing'}")
        print(f"         wav files: {len(wavs)}")

        if not (meta_ok and wav_ok):
            ok = False

    print(f"\n  Total spoof WAV files: {total_wavs}")
    expected_range = 380 <= total_wavs <= 420
    print(f"  [{'OK' if expected_range else 'FAIL'}] Expected ~400 WAV files")

    return ok and expected_range


def main() -> int:
    print("=" * 55)
    print("  VoiceGuard V3 — MLAAD-tiny spoof download")
    print("=" * 55)
    print(f"  Repo     : {REPO_ID} @ {REVISION}")
    print(f"  Target   : {LOCAL_DIR}")
    print(f"  Patterns : {len(ALLOW_PATTERNS)} folders (spoof only)")
    print()

    LOCAL_DIR.mkdir(parents=True, exist_ok=True)

    print("[->] Downloading selective subset (not full MLAAD-tiny)...")
    snapshot_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        revision=REVISION,
        allow_patterns=ALLOW_PATTERNS,
        local_dir=str(LOCAL_DIR),
    )

    print(f"[OK] Files saved under {LOCAL_DIR}")

    if verify_download(LOCAL_DIR):
        print("\n[OK] MLAAD-tiny spoof subset ready for V3 metadata setup.")
        return 0

    print("\n[!] Verification failed — check paths and network, then re-run.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
