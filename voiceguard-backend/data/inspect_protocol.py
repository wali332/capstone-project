from collections import Counter

PROTOCOL = r"C:\Users\walia\Downloads\ASVspoof5_protocols\ASVspoof5.train.tsv"

attack_counts = Counter()
label_counts = Counter()

with open(PROTOCOL, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split()

        if len(parts) < 9:
            continue

        label = parts[8]
        label_counts[label] += 1

        if label == "spoof":
            attack = parts[7]
            attack_counts[attack] += 1

print("Labels:")
for label, count in label_counts.items():
    print(f"{label}: {count}")

print("\nSpoof attack categories:")
for attack, count in sorted(attack_counts.items()):
    print(f"{attack}: {count}")