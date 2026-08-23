from pathlib import Path
import librosa

AUDIO_DIR = Path(r"C:\Users\walia\Downloads\flac_T_aa\flac_T")

files = list(AUDIO_DIR.glob("*.flac"))

print("Total FLAC files:", len(files))

print("\nFirst 10 files:")
for file in files[:10]:
    print(file.name)

print("\nChecking sample audio...\n")

for file in files[:5]:
    audio, sr = librosa.load(file, sr=None)

    duration = len(audio) / sr

    print(
        f"{file.name} | "
        f"Sample Rate: {sr} Hz | "
        f"Duration: {duration:.2f} sec | "
        f"Samples: {len(audio)}"
    )