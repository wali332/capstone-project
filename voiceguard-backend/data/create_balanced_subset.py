import csv
import random
from pathlib import Path
from collections import defaultdict

INPUT = Path("data/dataset_metadata.csv")
OUTPUT = Path("data/balanced_metadata.csv")

SEED = 42
SPOOF_PER_ATTACK = 475
BONAFIDE_COUNT = 3800

random.seed(SEED)

with open(INPUT, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

spoof_by_attack = defaultdict(list)
bonafide = []

for row in rows:
    if row["label"] == "spoof":
        spoof_by_attack[row["attack"]].append(row)
    elif row["label"] == "bonafide":
        bonafide.append(row)

selected = []

# Select equal number from every spoof attack category
for attack in sorted(spoof_by_attack):
    candidates = spoof_by_attack[attack]

    if len(candidates) < SPOOF_PER_ATTACK:
        raise ValueError(
            f"Not enough samples for {attack}: {len(candidates)}"
        )

    selected.extend(
        random.sample(candidates, SPOOF_PER_ATTACK)
    )

# Select bonafide samples
selected.extend(
    random.sample(bonafide, BONAFIDE_COUNT)
)

# Shuffle final dataset
random.shuffle(selected)

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["audio_id", "audio_path", "label", "attack"]
    )

    writer.writeheader()
    writer.writerows(selected)

print("Balanced dataset created.")
print("Total samples:", len(selected))
print("Spoof:", sum(x["label"] == "spoof" for x in selected))
print("Bonafide:", sum(x["label"] == "bonafide" for x in selected))

print("\nSpoof attack distribution:")
for attack in sorted(spoof_by_attack):
    count = sum(
        x["label"] == "spoof" and x["attack"] == attack
        for x in selected
    )
    print(f"{attack}: {count}")