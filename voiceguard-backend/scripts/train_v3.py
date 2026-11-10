"""
VoiceGuard V3 — CNN Training Script
===================================
Trains the same V2 CNN architecture on V3 spectrograms.
Does NOT modify train.py, V2 model, or V2 NPZ files.

Run from project root:
    python scripts/train_v3.py
"""

import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_PATH = BASE_DIR / "data" / "spectrograms" / "v3" / "train.npz"
VAL_PATH = BASE_DIR / "data" / "spectrograms" / "v3" / "validation.npz"
TEST_PATH = BASE_DIR / "data" / "spectrograms" / "v3" / "test.npz"

MODEL_PATH = BASE_DIR / "models" / "voiceguard_model_v3.h5"
CHECKPOINT_PATH = BASE_DIR / "models" / "voiceguard_model_v3_best.h5"
PLOT_PATH = BASE_DIR / "models" / "training_history_v3.png"

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)


def _compile_model(model):
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def build_model_v2(input_shape=(128, 128, 1)):
    """Exact V2 CNN architecture."""
    from tensorflow.keras import layers, models

    model = models.Sequential([
        layers.Input(shape=input_shape),

        layers.Conv2D(32, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.Conv2D(32, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.20),

        layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        layers.Conv2D(128, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.Conv2D(128, (3, 3), activation="relu", padding="same", dilation_rate=2),
        layers.BatchNormalization(),
        layers.Dropout(0.30),

        layers.Conv2D(256, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.Dropout(0.30),

        layers.GlobalAveragePooling2D(),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.5),
        layers.Dense(2, activation="softmax"),
    ])
    return _compile_model(model)


def load_split(path: Path):
    data = np.load(path)
    return data["X"], data["y"]


def best_epoch_from_history(history) -> tuple[int, float]:
    val_acc = history.history["val_accuracy"]
    best_idx = int(np.argmax(val_acc))
    return best_idx + 1, float(val_acc[best_idx])


def evaluate_test(model, X_test, y_test) -> dict:
    y_prob = model.predict(X_test, verbose=0)
    y_pred = np.argmax(y_prob, axis=1)

    acc = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average="binary", pos_label=1, zero_division=0)
    recall = recall_score(y_test, y_pred, average="binary", pos_label=1, zero_division=0)
    f1 = f1_score(y_test, y_pred, average="binary", pos_label=1, zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])

    return {
        "accuracy": acc,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confusion_matrix": cm,
        "y_pred": y_pred,
    }


def main() -> int:
    import tensorflow as tf

    print("=" * 55)
    print("  VoiceGuard — Model Training (V3)")
    print("=" * 55)

    for path in (TRAIN_PATH, VAL_PATH):
        if not path.exists():
            print(f"\n[!] Spectrogram data not found: {path}")
            print("    Run python scripts/preprocess_v3.py first.")
            return 1

    print(f"\n[->] Loading train spectrograms from {TRAIN_PATH}...")
    X_train, y_train = load_split(TRAIN_PATH)
    print(f"    Train: X={X_train.shape}, y={y_train.shape}")
    print(f"    Bonafide (0): {(y_train == 0).sum()}, Spoof (1): {(y_train == 1).sum()}")

    print(f"\n[->] Loading validation spectrograms from {VAL_PATH}...")
    X_val, y_val = load_split(VAL_PATH)
    print(f"    Val: X={X_val.shape}, y={y_val.shape}")
    print(f"    Bonafide (0): {(y_val == 0).sum()}, Spoof (1): {(y_val == 1).sum()}")

    model = build_model_v2()
    model.summary()
    print(f"\n    Parameters: {model.count_params():,}")

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=5, restore_best_weights=True, verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, verbose=1
        ),
        tf.keras.callbacks.ModelCheckpoint(
            str(CHECKPOINT_PATH), save_best_only=True, monitor="val_accuracy", verbose=1
        ),
    ]

    print("\n[->] Training...")
    t0 = time.perf_counter()
    history = model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=30,
        batch_size=32,
        callbacks=callbacks,
    )
    training_time_s = time.perf_counter() - t0

    model.save(str(MODEL_PATH))
    print(f"\n[OK] Model saved -> {MODEL_PATH}")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(history.history["accuracy"], label="train")
    ax1.plot(history.history["val_accuracy"], label="val")
    ax1.set_title("Accuracy")
    ax1.legend()
    ax2.plot(history.history["loss"], label="train")
    ax2.plot(history.history["val_loss"], label="val")
    ax2.set_title("Loss")
    ax2.legend()
    plt.tight_layout()
    plt.savefig(PLOT_PATH)
    print(f"[OK] Training plot saved -> {PLOT_PATH}")

    best_epoch, best_val_acc = best_epoch_from_history(history)
    val_loss, val_acc = model.evaluate(X_val, y_val, verbose=0)

    print("\n" + "=" * 55)
    print("  V3 training summary")
    print("=" * 55)
    print(f"  Training time        : {training_time_s / 60:.1f} min ({training_time_s:.1f} s)")
    print(f"  Best epoch           : {best_epoch}")
    print(f"  Best validation acc  : {best_val_acc * 100:.2f}%")
    print(f"  Final validation acc : {val_acc * 100:.2f}%")

    if not TEST_PATH.exists():
        print(f"\n[!] Test set not found: {TEST_PATH}")
        return 1

    print(f"\n[->] Evaluating on V3 test set: {TEST_PATH}")
    X_test, y_test = load_split(TEST_PATH)
    print(f"    Test: X={X_test.shape}, y={y_test.shape}")
    print(f"    Bonafide (0): {(y_test == 0).sum()}, Spoof (1): {(y_test == 1).sum()}")

    metrics = evaluate_test(model, X_test, y_test)
    cm = metrics["confusion_matrix"]

    print("\n" + "=" * 55)
    print("  V3 test results")
    print("=" * 55)
    print(f"  Test accuracy  : {metrics['accuracy'] * 100:.2f}%")
    print(f"  Precision      : {metrics['precision'] * 100:.2f}%  (spoof=positive)")
    print(f"  Recall         : {metrics['recall'] * 100:.2f}%  (spoof detection rate)")
    print(f"  F1             : {metrics['f1'] * 100:.2f}%")
    print("  Confusion matrix (rows=actual [bonafide, spoof], cols=pred [bonafide, spoof]):")
    print(f"    {cm.tolist()}")

    print("\n  Classification report:")
    print(
        classification_report(
            y_test,
            metrics["y_pred"],
            target_names=["bonafide (0)", "spoof (1)"],
            digits=4,
        )
    )

    print("\n" + "=" * 55)
    print("V3 MODEL CREATED: YES")
    print(f"MODEL PATH: {MODEL_PATH}")
    print(
        "TEST RESULTS: "
        f"accuracy={metrics['accuracy'] * 100:.2f}%, "
        f"precision={metrics['precision'] * 100:.2f}%, "
        f"recall={metrics['recall'] * 100:.2f}%, "
        f"F1={metrics['f1'] * 100:.2f}%, "
        f"confusion_matrix={cm.tolist()}"
    )
    print("=" * 55)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
