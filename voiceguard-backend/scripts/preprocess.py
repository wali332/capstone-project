"""
VoiceGuard — Batch Preprocessing Script
Runs all audio files through the full processing pipeline and saves
spectrograms as a compressed numpy archive for training.

Run: python scripts/preprocess.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from tqdm import tqdm
from audio_pipeline import process_audio

BASE_DIR    = Path(__file__).resolve().parent.parent
DATA_REAL   = BASE_DIR / "data" / "processed" / "real"
DATA_FAKE   = BASE_DIR / "data" / "processed" / "fake"
OUTPUT_PATH = BASE_DIR / "data" / "spectrograms.npz"

MAX_PER_CLASS = 5000


def process_folder(folder: Path, label: int, max_files: int = None):
    exts  = ["*.wav", "*.flac", "*.mp3"]
    files = []
    for e in exts:
        files.extend(folder.glob(e))
    if max_files:
        files = files[:max_files]

    label_name = "real" if label == 0 else "fake"
    print(f"\n[→] Processing {len(files)} {label_name} files...")

    X, y, skipped = [], [], 0
    for f in tqdm(files, desc=label_name):
        spec = process_audio(f, denoise=True, pre_emphasis=True, trim=True)
        if spec is not None:
            X.append(spec)
            y.append(label)
        else:
            skipped += 1

    if skipped:
        print(f"  [!] Skipped {skipped} files (corrupt / too short)")
    return X, y


def main():
    print("=" * 55)
    print("  VoiceGuard — Mel Spectrogram Preprocessing")
    print("=" * 55)

    real_files, fake_files = [], []
    for e in ["*.wav", "*.flac", "*.mp3"]:
        real_files.extend(DATA_REAL.glob(e))
        fake_files.extend(DATA_FAKE.glob(e))

    if not real_files or not fake_files:
        print(f"\n[!] No audio files found.")
        print(f"    Real → {DATA_REAL}")
        print(f"    Fake → {DATA_FAKE}")
        print("\n    Run: python scripts/download_dataset.py first.")
        return

    print(f"\n    Found {len(real_files)} real, {len(fake_files)} fake files")
    print(f"    Pipeline: trim → denoise → pre-emphasis → normalize → mel spec")

    X_real, y_real = process_folder(DATA_REAL, label=0, max_files=MAX_PER_CLASS)
    X_fake, y_fake = process_folder(DATA_FAKE, label=1, max_files=MAX_PER_CLASS)

    X = np.array(X_real + X_fake, dtype=np.float32)[..., np.newaxis]
    y = np.array(y_real + y_fake, dtype=np.int32)

    idx = np.random.permutation(len(X))
    X, y = X[idx], y[idx]

    np.savez_compressed(OUTPUT_PATH, X=X, y=y)
    print(f"\n[✓] Saved {len(X)} spectrograms → {OUTPUT_PATH}")
    print(f"    Shape : X={X.shape}, y={y.shape}")
    print(f"    Real  : {(y==0).sum()}, Fake: {(y==1).sum()}")
    print(f"\n[✓] Done! Run next: python scripts/train.py")


if __name__ == "__main__":
    main()
