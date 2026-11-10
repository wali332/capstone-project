"""
Temporary read-only V3 test-set verification.
Does NOT modify model, training code, backend, or existing evaluate_v3.py output.
Replicates evaluate_v3.py test.npz methodology exactly.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "voiceguard_model_v3_best.h5"
TEST_NPZ = BASE_DIR / "data" / "spectrograms" / "v3" / "test.npz"
SPLIT_CSV = BASE_DIR / "data" / "v3_splits" / "test.csv"


def label_name(y: int) -> str:
    return "bonafide" if y == 0 else "spoof"


def pred_name(y_pred: int) -> str:
    return "HUMAN VOICE" if y_pred == 0 else "AI GENERATED"


def main() -> int:
    if not MODEL_PATH.exists():
        print(f"MISSING MODEL: {MODEL_PATH}")
        return 1
    if not TEST_NPZ.exists():
        print(f"MISSING TEST NPZ: {TEST_NPZ}")
        return 1

    data = np.load(TEST_NPZ, allow_pickle=True)
    X_test, y_test = data["X"], data["y"]
    ids = data["ids"] if "ids" in data else None

    model = tf.keras.models.load_model(str(MODEL_PATH))
    y_prob = model.predict(X_test, verbose=0)
    y_pred = np.argmax(y_prob, axis=1)

    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    human_n = int((y_test == 0).sum())
    spoof_n = int((y_test == 1).sum())
    total = int(len(y_test))

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="binary", pos_label=1, zero_division=0)
    rec = recall_score(y_test, y_pred, average="binary", pos_label=1, zero_division=0)
    f1 = f1_score(y_test, y_pred, average="binary", pos_label=1, zero_division=0)

    print("=== FRESH RUN ===")
    print(f"model={MODEL_PATH}")
    print(f"test_npz={TEST_NPZ}")
    print(f"split_csv={SPLIT_CSV} exists={SPLIT_CSV.exists()}")
    print(f"total={total} human={human_n} spoof={spoof_n}")
    print(f"TP={tp} TN={tn} FP={fp} FN={fn}")
    print(f"accuracy={acc*100:.4f}% precision={prec*100:.4f}% recall={rec*100:.4f}% f1={f1*100:.4f}%")
    print(f"cm={cm.tolist()}")

    # Sample predictions: one bonafide, one spoof (first in test set by label)
    if ids is not None:
        for want_label in (0, 1):
            idxs = np.where(y_test == want_label)[0]
            if len(idxs) == 0:
                continue
            i = int(idxs[0])
            bonafide_p, spoof_p = float(y_prob[i, 0]), float(y_prob[i, 1])
            confidence = int(round(max(bonafide_p, spoof_p) * 100))
            correct = y_pred[i] == y_test[i]
            print(
                "SAMPLE",
                ids[i],
                f"true={label_name(int(y_test[i]))}",
                f"pred={pred_name(int(y_pred[i]))}",
                f"bonafide_prob={bonafide_p:.6f}",
                f"spoof_prob={spoof_p:.6f}",
                f"confidence={confidence}%",
                f"correct={correct}",
            )

    # Also print one misclassified of each type if available
    for want_label, kind in ((0, "FP"), (1, "FN")):
        mask = (y_test == want_label) & (y_pred != y_test)
        idxs = np.where(mask)[0]
        if len(idxs) == 0:
            print(f"MISSED_{kind}=none")
            continue
        i = int(idxs[0])
        bonafide_p, spoof_p = float(y_prob[i, 0]), float(y_prob[i, 1])
        confidence = int(round(max(bonafide_p, spoof_p) * 100))
        print(
            f"MISSED_{kind}",
            ids[i] if ids is not None else i,
            f"true={label_name(int(y_test[i]))}",
            f"pred={pred_name(int(y_pred[i]))}",
            f"confidence={confidence}%",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
