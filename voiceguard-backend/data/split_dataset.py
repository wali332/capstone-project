import csv
from pathlib import Path
from sklearn.model_selection import train_test_split

INPUT = Path("data/balanced_metadata.csv")
OUTPUT_DIR = Path("data/splits")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with open(INPUT, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

# First: 70% train, 30% temporary
train_rows, temp_rows = train_test_split(
    rows,
    test_size=0.30,
    random_state=42,
    stratify=[row["label"] for row in rows]
)

# Then: split remaining 30% equally
val_rows, test_rows = train_test_split(
    temp_rows,
    test_size=0.50,
    random_state=42,
    stratify=[row["label"] for row in temp_rows]
)

def save_csv(path, data):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["audio_id", "audio_path", "label", "attack"]
        )
        writer.writeheader()
        writer.writerows(data)

save_csv(OUTPUT_DIR / "train.csv", train_rows)
save_csv(OUTPUT_DIR / "validation.csv", val_rows)
save_csv(OUTPUT_DIR / "test.csv", test_rows)

print("Dataset split complete.")
print("Train:", len(train_rows))
print("Validation:", len(val_rows))
print("Test:", len(test_rows))

for name, data in [
    ("Train", train_rows),
    ("Validation", val_rows),
    ("Test", test_rows)
]:
    spoof = sum(x["label"] == "spoof" for x in data)
    bonafide = sum(x["label"] == "bonafide" for x in data)

    print(f"\n{name}:")
    print("  Spoof:", spoof)
    print("  Bonafide:", bonafide)