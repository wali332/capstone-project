"""
VoiceGuard — CNN Training Script
Trains a lightweight CNN on 128x128 mel spectrograms.
Saves the trained model to models/voiceguard_model.h5

Run: python scripts/train.py
"""

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "spectrograms.npz"
MODEL_PATH = BASE_DIR / "models" / "voiceguard_model.h5"
PLOT_PATH  = BASE_DIR / "models" / "training_history.png"
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)


def build_model(input_shape=(128, 128, 1)):
    """
    Lightweight CNN — fast to train on CPU/laptop.
    Architecture:
      Conv2D(32) → MaxPool → Conv2D(64) → MaxPool →
      Conv2D(128) → MaxPool → Flatten → Dense(128) → Dropout → Dense(2, softmax)
    """
    import tensorflow as tf
    from tensorflow.keras import layers, models

    model = models.Sequential([
        layers.Input(shape=input_shape),

        # Block 1
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        # Block 2
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        # Block 3
        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        # Classifier head
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(2, activation='softmax'),   # [real_prob, fake_prob]
    ])

    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


def main():
    import tensorflow as tf
    from sklearn.model_selection import train_test_split

    print("=" * 55)
    print("  VoiceGuard — Model Training")
    print("=" * 55)

    if not DATA_PATH.exists():
        print(f"\n[!] Spectrogram data not found: {DATA_PATH}")
        print("    Run python scripts/preprocess.py first.")
        return

    print(f"\n[→] Loading spectrograms from {DATA_PATH}...")
    data = np.load(DATA_PATH)
    X, y = data['X'], data['y']
    print(f"    Loaded: X={X.shape}, y={y.shape}")
    print(f"    Real (0): {(y==0).sum()}, Fake (1): {(y==1).sum()}")

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n    Train: {len(X_train)}, Val: {len(X_val)}")

    model = build_model()
    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor='val_accuracy', patience=5, restore_best_weights=True, verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=3, verbose=1
        ),
        tf.keras.callbacks.ModelCheckpoint(
            str(MODEL_PATH), save_best_only=True, monitor='val_accuracy', verbose=1
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
    model.save(str(MODEL_PATH))
    print(f"\n[✓] Model saved → {MODEL_PATH}")

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
    plt.savefig(PLOT_PATH)
    print(f"[✓] Training plot saved → {PLOT_PATH}")

    # Final evaluation
    loss, acc = model.evaluate(X_val, y_val, verbose=0)
    print(f"\n[✓] Final validation accuracy: {acc*100:.1f}%")
    print("\n[✓] Done! Run next: python main.py  (to start the API)")


if __name__ == "__main__":
    main()
