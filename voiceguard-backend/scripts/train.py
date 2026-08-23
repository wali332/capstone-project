"""
VoiceGuard — CNN Training Script
Trains a CNN on 128x128 mel spectrograms.

Run:
  python scripts/train.py          # CNN v2 (default)
  python scripts/train.py --v1     # original baseline CNN
"""

import argparse
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_PATH = BASE_DIR / "data" / "spectrograms" / "train.npz"
VAL_PATH   = BASE_DIR / "data" / "spectrograms" / "validation.npz"
TEST_PATH  = BASE_DIR / "data" / "spectrograms" / "test.npz"

MODEL_PATH_V1 = BASE_DIR / "models" / "voiceguard_model.h5"
MODEL_PATH_V2 = BASE_DIR / "models" / "voiceguard_model_v2.h5"
CHECKPOINT_PATH_V2 = BASE_DIR / "models" / "voiceguard_model_v2_best.h5"
PLOT_PATH_V1  = BASE_DIR / "models" / "training_history.png"
PLOT_PATH_V2  = BASE_DIR / "models" / "training_history_v2.png"

MODEL_PATH_V1.parent.mkdir(parents=True, exist_ok=True)


def _compile_model(model):
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'],
    )
    return model


def build_model_v1(input_shape=(128, 128, 1)):
    """Original baseline CNN (~4.29M params). Flatten -> Dense(128) head."""
    from tensorflow.keras import layers, models

    model = models.Sequential([
        layers.Input(shape=input_shape),

        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(2, activation='softmax'),
    ])
    return _compile_model(model)


def build_model_v2(input_shape=(128, 128, 1)):
    """
    CNN v2 (~618K params). Stacked conv blocks, dilated conv, GAP head.
    Input (128,128,1) -> softmax(2). Same labels: 0=bonafide, 1=spoof.
    """
    from tensorflow.keras import layers, models

    model = models.Sequential([
        layers.Input(shape=input_shape),

        # Block 1: 128x128 -> 64x64
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.20),

        # Block 2: 64x64 -> 32x32
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        # Block 3: 32x32 (dilated conv for wider time-frequency context)
        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.Conv2D(128, (3, 3), activation='relu', padding='same', dilation_rate=2),
        layers.BatchNormalization(),
        layers.Dropout(0.30),

        # Block 4: 32x32 high-level maps
        layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.Dropout(0.30),

        # Head: GAP replaces Flatten -> Dense(32768->128)
        layers.GlobalAveragePooling2D(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(2, activation='softmax'),
    ])
    return _compile_model(model)


def build_model(version=2, input_shape=(128, 128, 1)):
    if version == 1:
        return build_model_v1(input_shape)
    return build_model_v2(input_shape)


def load_split(path: Path):
    data = np.load(path)
    return data["X"], data["y"]


def main():
    import tensorflow as tf

    parser = argparse.ArgumentParser(description="VoiceGuard CNN training")
    parser.add_argument("--v1", action="store_true", help="Train baseline v1 CNN instead of v2")
    args = parser.parse_args()

    version = 1 if args.v1 else 2
    model_path = MODEL_PATH_V1 if version == 1 else MODEL_PATH_V2
    checkpoint_path = model_path if version == 1 else CHECKPOINT_PATH_V2
    plot_path = PLOT_PATH_V1 if version == 1 else PLOT_PATH_V2
    version_label = "v1 (baseline)" if version == 1 else "v2"

    print("=" * 55)
    print(f"  VoiceGuard — Model Training ({version_label})")
    print("=" * 55)

    for path in (TRAIN_PATH, VAL_PATH):
        if not path.exists():
            print(f"\n[!] Spectrogram data not found: {path}")
            print("    Run python scripts/preprocess.py first.")
            return

    print(f"\n[→] Loading train spectrograms from {TRAIN_PATH}...")
    X_train, y_train = load_split(TRAIN_PATH)
    print(f"    Train: X={X_train.shape}, y={y_train.shape}")
    print(f"    Bonafide (0): {(y_train == 0).sum()}, Spoof (1): {(y_train == 1).sum()}")

    print(f"\n[→] Loading validation spectrograms from {VAL_PATH}...")
    X_val, y_val = load_split(VAL_PATH)
    print(f"    Val: X={X_val.shape}, y={y_val.shape}")
    print(f"    Bonafide (0): {(y_val == 0).sum()}, Spoof (1): {(y_val == 1).sum()}")

    model = build_model(version=version)
    model.summary()
    print(f"\n    Parameters: {model.count_params():,}")

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor='val_accuracy', patience=5, restore_best_weights=True, verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=3, verbose=1
        ),
        tf.keras.callbacks.ModelCheckpoint(
            str(checkpoint_path), save_best_only=True, monitor='val_accuracy', verbose=1
        ),
    ]

    print(f"\n[→] Training...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=30,
        batch_size=32,
        callbacks=callbacks,
    )

    # Save final model
    model.save(str(model_path))
    print(f"\n[✓] Model saved → {model_path}")

    # Plot training curves
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(history.history['accuracy'], label='train')
    ax1.plot(history.history['val_accuracy'], label='val')
    ax1.set_title('Accuracy')
    ax1.legend()
    ax2.plot(history.history['loss'], label='train')
    ax2.plot(history.history['val_loss'], label='val')
    ax2.set_title('Loss')
    ax2.legend()
    plt.tight_layout()
    plt.savefig(plot_path)
    print(f"[✓] Training plot saved → {plot_path}")

    # Final validation evaluation
    loss, acc = model.evaluate(X_val, y_val, verbose=0)
    print(f"\n[✓] Final validation accuracy: {acc*100:.1f}%")

    # Held-out test evaluation (not used during training)
    if TEST_PATH.exists():
        print(f"\n[→] Evaluating on held-out test set: {TEST_PATH}")
        X_test, y_test = load_split(TEST_PATH)
        test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
        print(f"    Test: X={X_test.shape}, y={y_test.shape}")
        print(f"    Bonafide (0): {(y_test == 0).sum()}, Spoof (1): {(y_test == 1).sum()}")
        print(f"[✓] Final test accuracy: {test_acc*100:.1f}%")
    else:
        print(f"\n[!] Test set not found: {TEST_PATH}")
        print("    Run python scripts/preprocess.py to generate test.npz.")

    print("\n[✓] Done! Run next: python main.py  (to start the API)")


if __name__ == "__main__":
    main()
