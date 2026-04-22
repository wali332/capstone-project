"""
VoiceGuard — Dataset Setup Script
Downloads a ready-to-use subset from the FakeAVCeleb / FOR dataset mirror.
Uses the FOR-norm dataset (Fake-or-Real), which is small (~600MB) and
perfectly suited for binary real vs fake audio classification.

Run: python scripts/download_dataset.py
"""

import os
import zipfile
import shutil
import urllib.request
from pathlib import Path
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_REAL = BASE_DIR / "data" / "processed" / "real"
DATA_FAKE = BASE_DIR / "data" / "processed" / "fake"

DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_REAL.mkdir(parents=True, exist_ok=True)
DATA_FAKE.mkdir(parents=True, exist_ok=True)

# FOR-norm dataset — binary real/fake, English speech, ~600MB
# Hosted on Zenodo (open access, no login needed)
DATASET_URL = "https://zenodo.org/record/4319978/files/for-norm.zip"
ZIP_PATH = DATA_RAW / "for-norm.zip"
EXTRACT_PATH = DATA_RAW / "for-norm"


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_dataset():
    if ZIP_PATH.exists():
        print(f"[✓] ZIP already downloaded: {ZIP_PATH}")
    else:
        print(f"[→] Downloading FOR-norm dataset (~600MB)...")
        print(f"    URL: {DATASET_URL}")
        with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc="Downloading") as t:
            urllib.request.urlretrieve(DATASET_URL, ZIP_PATH, reporthook=t.update_to)
        print(f"[✓] Downloaded to {ZIP_PATH}")


def extract_dataset():
    if EXTRACT_PATH.exists():
        print(f"[✓] Already extracted: {EXTRACT_PATH}")
        return
    print(f"[→] Extracting ZIP...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        zf.extractall(DATA_RAW)
    print(f"[✓] Extracted to {EXTRACT_PATH}")


def organise_files():
    """
    FOR-norm structure:
      for-norm/
        training/
          real/   ← .wav files
          fake/   ← .wav files
        testing/
          real/
          fake/
        validation/
          real/
          fake/

    We merge all splits into data/processed/real and data/processed/fake
    so our training script controls the split itself.
    """
    real_count = 0
    fake_count = 0

    for split in ["training", "testing", "validation"]:
        for label in ["real", "fake"]:
            src_dir = EXTRACT_PATH / split / label
            if not src_dir.exists():
                print(f"[!] Not found: {src_dir} — skipping")
                continue

            dest_dir = DATA_REAL if label == "real" else DATA_FAKE
            files = list(src_dir.glob("*.wav")) + list(src_dir.glob("*.flac"))

            print(f"[→] Copying {len(files)} {label} files from {split}...")
            for f in files:
                dest = dest_dir / f"{split}_{f.name}"
                if not dest.exists():
                    shutil.copy2(f, dest)
                if label == "real":
                    real_count += 1
                else:
                    fake_count += 1

    print(f"\n[✓] Dataset organised:")
    print(f"    Real files : {real_count}")
    print(f"    Fake files : {fake_count}")
    print(f"    Total      : {real_count + fake_count}")
    print(f"\n    Real → {DATA_REAL}")
    print(f"    Fake → {DATA_FAKE}")


def main():
    print("=" * 55)
    print("  VoiceGuard — Dataset Setup")
    print("=" * 55)
    download_dataset()
    extract_dataset()
    organise_files()
    print("\n[✓] All done! Run next: python scripts/preprocess.py")


if __name__ == "__main__":
    main()
