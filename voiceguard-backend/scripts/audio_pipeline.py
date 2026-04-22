"""
VoiceGuard — Audio Processing Pipeline
========================================
Full signal processing chain:
  1. Load & convert to mono
  2. Resample to target SR
  3. Trim silence from edges
  4. Spectral noise reduction (stationary noise floor estimation)
  5. Pre-emphasis filter (boost high frequencies)
  6. RMS normalization
  7. Center-pad or crop to fixed duration
  8. Mel spectrogram extraction
  9. Convert to dB scale
 10. Normalize spectrogram to [0, 1]
 11. Save as 128x128 PNG + numpy array

Run standalone to process a single file and visualize the result:
    python scripts/audio_pipeline.py path/to/audio.wav

Run as a module from preprocess.py for batch processing.
"""

import io
import numpy as np
import librosa
import librosa.effects
from pathlib import Path
from typing import Optional

# ── Config (single source of truth — imported by train.py and app.py) ─────────
SAMPLE_RATE  = 16000      # 16kHz is standard for speech processing
DURATION     = 4.0        # seconds per clip
N_MELS       = 128        # mel filter banks
HOP_LENGTH   = 256        # ~16ms hop at 16kHz
N_FFT        = 1024       # FFT window size
F_MIN        = 50         # ignore below 50Hz (not speech)
F_MAX        = 8000       # ignore above 8kHz (above speech range)
IMG_SIZE     = 128        # output spectrogram size (square)
TOP_DB       = 80         # dynamic range cap for dB conversion


# ── Step 1-2: Load + resample ──────────────────────────────────────────────────
def load_audio(source, sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int]:
    """
    Load audio from a file path or bytes object.
    Always returns mono float32 at target sample rate.
    """
    if isinstance(source, (str, Path)):
        y, _ = librosa.load(str(source), sr=sr, mono=True)
    elif isinstance(source, (bytes, bytearray)):
        y, _ = librosa.load(io.BytesIO(source), sr=sr, mono=True)
    else:
        # Already a numpy array
        y = source.astype(np.float32)
    return y, sr


# ── Step 3: Trim silence ───────────────────────────────────────────────────────
def trim_silence(y: np.ndarray, top_db: int = 30) -> np.ndarray:
    """
    Remove leading and trailing silence.
    top_db: silence threshold in dB below peak (higher = more aggressive trim)
    """
    y_trimmed, _ = librosa.effects.trim(y, top_db=top_db)
    # Fallback: if trim removes everything, return original
    return y_trimmed if len(y_trimmed) > 0 else y


# ── Step 4: Noise reduction ────────────────────────────────────────────────────
def reduce_noise(y: np.ndarray, sr: int = SAMPLE_RATE,
                 noise_sample_duration: float = 0.3) -> np.ndarray:
    """
    Stationary noise reduction using spectral subtraction.

    Method:
    - Estimate noise profile from the first N seconds (assumed to be
      background/silence before speech starts)
    - Subtract the mean noise spectrum from all frames
    - Apply soft masking so we don't create musical noise artifacts

    This works well for:
    - Microphone hiss
    - Room background noise
    - Constant fan/AC noise

    It does NOT help with:
    - Non-stationary noise (traffic, voices in background)
    - Very short clips where there's no clean noise sample
    """
    noise_samples = int(sr * noise_sample_duration)

    # Need enough audio to estimate noise — skip if too short
    if len(y) < noise_samples * 2:
        return y

    # Estimate noise from first noise_sample_duration seconds
    noise_clip = y[:noise_samples]

    # STFT of full signal and noise
    D_full  = librosa.stft(y,          n_fft=N_FFT, hop_length=HOP_LENGTH)
    D_noise = librosa.stft(noise_clip, n_fft=N_FFT, hop_length=HOP_LENGTH)

    # Magnitude spectra
    mag_full  = np.abs(D_full)
    mag_noise = np.abs(D_noise)

    # Mean noise profile across time
    noise_profile = np.mean(mag_noise, axis=1, keepdims=True)

    # Soft spectral subtraction with over-subtraction factor
    # alpha=2.0 = moderate, higher = more aggressive noise removal
    alpha = 2.0
    mag_denoised = mag_full - alpha * noise_profile

    # Soft mask: keep original where signal is strong, suppress where it's weak
    # This prevents the "musical noise" artifact of hard subtraction
    mask = mag_denoised / (mag_full + 1e-8)
    mask = np.clip(mask, 0.1, 1.0)   # floor at 0.1 to preserve some residual

    D_denoised = D_full * mask
    y_denoised = librosa.istft(D_denoised, hop_length=HOP_LENGTH,
                                length=len(y))
    return y_denoised.astype(np.float32)


# ── Step 5: Pre-emphasis ───────────────────────────────────────────────────────
def apply_pre_emphasis(y: np.ndarray, coeff: float = 0.97) -> np.ndarray:
    """
    High-pass filter that boosts high-frequency content.
    Compensates for the natural roll-off of speech signals.
    Makes high-frequency artifacts from TTS systems more visible
    in the spectrogram — improving fake detection.

    y[n] = y[n] - coeff * y[n-1]
    coeff=0.97 is the standard value for speech processing.
    """
    return np.append(y[0], y[1:] - coeff * y[:-1]).astype(np.float32)


# ── Step 6: RMS normalization ──────────────────────────────────────────────────
def normalize_rms(y: np.ndarray, target_rms: float = 0.05) -> np.ndarray:
    """
    Normalize audio to a consistent RMS (loudness) level.
    This ensures the CNN sees consistent amplitude ranges regardless
    of how loud/quiet the original recording was.

    target_rms=0.05 keeps peaks well below clipping at ±1.0
    """
    rms = np.sqrt(np.mean(y ** 2))
    if rms < 1e-8:
        return y   # silence — don't divide by zero
    y_normalized = y * (target_rms / rms)
    # Hard clip to prevent any remaining peaks from clipping
    return np.clip(y_normalized, -1.0, 1.0).astype(np.float32)


# ── Step 7: Fixed-length padding/cropping ─────────────────────────────────────
def fix_length(y: np.ndarray, sr: int = SAMPLE_RATE,
               duration: float = DURATION) -> np.ndarray:
    """
    Crop or center-pad audio to exactly `duration` seconds.
    Center-padding puts silence equally on both sides so the speech
    stays centered in the spectrogram rather than left-aligned.
    """
    target_len = int(sr * duration)
    current_len = len(y)

    if current_len >= target_len:
        # Crop from center
        start = (current_len - target_len) // 2
        return y[start:start + target_len]
    else:
        # Center pad with zeros
        pad_total = target_len - current_len
        pad_left  = pad_total // 2
        pad_right = pad_total - pad_left
        return np.pad(y, (pad_left, pad_right), mode='constant').astype(np.float32)


# ── Step 8-10: Mel spectrogram ─────────────────────────────────────────────────
def extract_melspec(y: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Extract mel spectrogram and convert to dB scale.

    Returns a 2D float32 array normalized to [0, 1].
    Shape: (N_MELS, time_frames) before resizing.
    """
    mel = librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_mels=N_MELS,
        fmin=F_MIN,
        fmax=F_MAX,
        power=2.0,       # power spectrogram (not magnitude)
    )

    # Convert to dB scale — this is perceptually more natural
    # and gives better dynamic range for visualization + CNN
    mel_db = librosa.power_to_db(mel, ref=np.max, top_db=TOP_DB)

    # Normalize to [0, 1]
    mel_norm = (mel_db - mel_db.min()) / (mel_db.max() - mel_db.min() + 1e-8)
    return mel_norm.astype(np.float32)


# ── Step 11: Resize to square ──────────────────────────────────────────────────
def resize_spec(spec: np.ndarray, size: int = IMG_SIZE) -> np.ndarray:
    """Resize spectrogram to size x size using bilinear interpolation."""
    from PIL import Image
    img = Image.fromarray((spec * 255).astype(np.uint8))
    img = img.resize((size, size), Image.BILINEAR)
    return np.array(img, dtype=np.float32) / 255.0


# ── Full pipeline ──────────────────────────────────────────────────────────────
def process_audio(
    source,
    denoise:       bool  = True,
    pre_emphasis:  bool  = True,
    trim:          bool  = True,
    verbose:       bool  = False,
) -> Optional[np.ndarray]:
    """
    Full pipeline: source (path or bytes) → 128x128 mel spectrogram numpy array.

    Returns None if processing fails.
    The returned array has shape (128, 128) with values in [0, 1].
    For CNN input, add channel dim: arr[..., np.newaxis] → (128, 128, 1)
    """
    try:
        y, sr = load_audio(source)
        if verbose: print(f"  Loaded: {len(y)/sr:.2f}s at {sr}Hz")

        if trim:
            y = trim_silence(y)
            if verbose: print(f"  After trim: {len(y)/sr:.2f}s")

        if denoise:
            y = reduce_noise(y, sr)
            if verbose: print(f"  Noise reduced")

        if pre_emphasis:
            y = apply_pre_emphasis(y)
            if verbose: print(f"  Pre-emphasis applied")

        y = normalize_rms(y)
        if verbose: print(f"  RMS normalized")

        y = fix_length(y, sr)
        if verbose: print(f"  Fixed to {DURATION}s ({len(y)} samples)")

        spec = extract_melspec(y, sr)
        if verbose: print(f"  Mel spectrogram: {spec.shape}")

        spec = resize_spec(spec, IMG_SIZE)
        if verbose: print(f"  Resized to {spec.shape}")

        return spec

    except Exception as e:
        if verbose: print(f"  [!] Pipeline failed: {e}")
        return None


# ── Standalone: visualize a single file ───────────────────────────────────────
def visualize_pipeline(filepath: str):
    """
    Process one file and show before/after spectrograms + waveform.
    Run: python scripts/audio_pipeline.py myfile.wav
    """
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec

    path = Path(filepath)
    print(f"\nProcessing: {path.name}")
    print("=" * 55)

    # Load raw
    y_raw, sr = load_audio(path)
    duration_raw = len(y_raw) / sr
    print(f"  Original: {duration_raw:.2f}s at {sr}Hz")

    # Step by step for visualization
    y_trim     = trim_silence(y_raw)
    y_denoised = reduce_noise(y_trim, sr)
    y_emph     = apply_pre_emphasis(y_denoised)
    y_norm     = normalize_rms(y_emph)
    y_fixed    = fix_length(y_norm, sr)

    spec_raw     = extract_melspec(fix_length(normalize_rms(y_raw), sr))
    spec_final   = extract_melspec(y_fixed)
    spec_resized = resize_spec(spec_final)

    # Plot
    fig = plt.figure(figsize=(16, 10), facecolor='#0D0D0F')
    fig.suptitle(f'VoiceGuard Audio Pipeline — {path.name}',
                 color='white', fontsize=14, fontweight='bold', y=0.98)

    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.5, wspace=0.35)

    plot_cfg = dict(facecolor='#141417')
    label_cfg = dict(color='#888', fontsize=8)
    title_cfg = dict(color='white', fontsize=10, fontweight='bold', pad=8)

    # Row 1: Waveforms
    ax1 = fig.add_subplot(gs[0, 0], **plot_cfg)
    t_raw = np.linspace(0, len(y_raw)/sr, len(y_raw))
    ax1.plot(t_raw, y_raw, color='#6C63FF', linewidth=0.4, alpha=0.8)
    ax1.set_title('1. Raw waveform', **title_cfg)
    ax1.set_xlabel('Time (s)', **label_cfg)
    ax1.set_ylabel('Amplitude', **label_cfg)
    ax1.tick_params(colors='#888', labelsize=7)
    ax1.spines[:].set_color('#2A2A30')

    ax2 = fig.add_subplot(gs[0, 1], **plot_cfg)
    t_trim = np.linspace(0, len(y_trim)/sr, len(y_trim))
    ax2.plot(t_trim, y_trim, color='#6C63FF', linewidth=0.4, alpha=0.8)
    ax2.set_title('2. Silence trimmed', **title_cfg)
    ax2.set_xlabel('Time (s)', **label_cfg)
    ax2.tick_params(colors='#888', labelsize=7)
    ax2.spines[:].set_color('#2A2A30')

    ax3 = fig.add_subplot(gs[0, 2], **plot_cfg)
    t_fixed = np.linspace(0, DURATION, len(y_fixed))
    ax3.plot(t_fixed, y_fixed, color='#00E5A0', linewidth=0.4, alpha=0.8)
    ax3.set_title(f'3. Denoised + normalized ({DURATION}s)', **title_cfg)
    ax3.set_xlabel('Time (s)', **label_cfg)
    ax3.tick_params(colors='#888', labelsize=7)
    ax3.spines[:].set_color('#2A2A30')

    # Row 2: Spectrograms
    ax4 = fig.add_subplot(gs[1, 0], **plot_cfg)
    img4 = ax4.imshow(spec_raw, aspect='auto', origin='lower',
                      cmap='magma', interpolation='nearest')
    ax4.set_title('4. Raw mel spectrogram', **title_cfg)
    ax4.set_xlabel('Time frames', **label_cfg)
    ax4.set_ylabel('Mel bins', **label_cfg)
    ax4.tick_params(colors='#888', labelsize=7)
    plt.colorbar(img4, ax=ax4, format='%.1f').ax.tick_params(colors='#888', labelsize=7)

    ax5 = fig.add_subplot(gs[1, 1], **plot_cfg)
    img5 = ax5.imshow(spec_final, aspect='auto', origin='lower',
                      cmap='magma', interpolation='nearest')
    ax5.set_title('5. Processed mel spectrogram', **title_cfg)
    ax5.set_xlabel('Time frames', **label_cfg)
    ax5.set_ylabel('Mel bins', **label_cfg)
    ax5.tick_params(colors='#888', labelsize=7)
    plt.colorbar(img5, ax=ax5, format='%.1f').ax.tick_params(colors='#888', labelsize=7)

    ax6 = fig.add_subplot(gs[1, 2], **plot_cfg)
    img6 = ax6.imshow(spec_resized, aspect='auto', origin='lower',
                      cmap='magma', interpolation='nearest')
    ax6.set_title(f'6. Final {IMG_SIZE}×{IMG_SIZE} input to CNN', **title_cfg)
    ax6.set_xlabel('Pixel (x)', **label_cfg)
    ax6.set_ylabel('Pixel (y)', **label_cfg)
    ax6.tick_params(colors='#888', labelsize=7)
    plt.colorbar(img6, ax=ax6, format='%.1f').ax.tick_params(colors='#888', labelsize=7)

    # Row 3: Frequency analysis
    ax7 = fig.add_subplot(gs[2, 0], **plot_cfg)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)
    D_raw  = np.abs(librosa.stft(fix_length(normalize_rms(y_raw), sr),
                                  n_fft=N_FFT, hop_length=HOP_LENGTH))
    D_proc = np.abs(librosa.stft(y_fixed, n_fft=N_FFT, hop_length=HOP_LENGTH))
    ax7.semilogy(freqs, np.mean(D_raw,  axis=1), color='#FF4D6D',
                 linewidth=1, label='raw',       alpha=0.8)
    ax7.semilogy(freqs, np.mean(D_proc, axis=1), color='#00E5A0',
                 linewidth=1, label='processed', alpha=0.8)
    ax7.set_title('7. Mean frequency spectrum', **title_cfg)
    ax7.set_xlabel('Frequency (Hz)', **label_cfg)
    ax7.set_ylabel('Magnitude', **label_cfg)
    ax7.tick_params(colors='#888', labelsize=7)
    ax7.spines[:].set_color('#2A2A30')
    ax7.legend(fontsize=7, facecolor='#141417', labelcolor='white')
    ax7.set_xlim(0, sr // 2)

    # Pipeline summary box
    ax8 = fig.add_subplot(gs[2, 1:], **plot_cfg)
    ax8.axis('off')
    summary = (
        f"Pipeline summary\n"
        f"{'─'*38}\n"
        f"Sample rate   :  {sr} Hz\n"
        f"Duration      :  {DURATION}s ({int(sr*DURATION)} samples)\n"
        f"Mel bands     :  {N_MELS}\n"
        f"FFT size      :  {N_FFT}\n"
        f"Hop length    :  {HOP_LENGTH} ({HOP_LENGTH/sr*1000:.1f}ms)\n"
        f"Freq range    :  {F_MIN}–{F_MAX} Hz\n"
        f"Output shape  :  {IMG_SIZE}×{IMG_SIZE}×1\n"
        f"{'─'*38}\n"
        f"Silence trim  :  yes (30dB threshold)\n"
        f"Noise reduce  :  spectral subtraction\n"
        f"Pre-emphasis  :  coeff=0.97\n"
        f"Normalization :  RMS target=0.05\n"
    )
    ax8.text(0.05, 0.95, summary, transform=ax8.transAxes,
             fontsize=8.5, verticalalignment='top',
             fontfamily='monospace', color='#aaa',
             bbox=dict(boxstyle='round', facecolor='#0D0D0F',
                       edgecolor='#2A2A30', alpha=0.8))

    out_path = path.parent / f"{path.stem}_pipeline.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight',
                facecolor='#0D0D0F', edgecolor='none')
    print(f"\n[✓] Saved visualization → {out_path}")
    plt.show()
    print("[✓] Done!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python scripts/audio_pipeline.py path/to/audio.wav")
        print("\nThis will:")
        print("  - Process the audio through the full pipeline")
        print("  - Show a 7-panel visualization of each step")
        print("  - Save the visualization as a PNG next to your audio file")
        sys.exit(1)
    visualize_pipeline(sys.argv[1])
