from pathlib import Path
import csv

AUDIO_DIR = Path(r"C:\Users\walia\Downloads\flac_T_aa\flac_T")
PROTOCOL = Path(r"C:\Users\walia\Downloads\ASVspoof5_protocols\ASVspoof5.train.tsv")
OUTPUT = Path("data/dataset_metadata.csv")

rows = []

with open(PROTOCOL, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split()

        if len(parts) < 9:
            continue

        audio_id = parts[1]
        attack = parts[7]
        label = parts[8]

        audio_path = AUDIO_DIR / f"{audio_id}.flac"

        if audio_path.exists():
            rows.append({
                "audio_id": audio_id,
                "audio_path": str(audio_path),
                "label": label,
                "attack": attack
            })

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["audio_id", "audio_path", "label", "attack"]
    )
    writer.writeheader()
    writer.writerows(rows)

print("Matched audio files:", len(rows))

spoof = sum(r["label"] == "spoof" for r in rows)
bonafide = sum(r["label"] == "bonafide" for r in rows)

print("Spoof:", spoof)
print("Bonafide:", bonafide)