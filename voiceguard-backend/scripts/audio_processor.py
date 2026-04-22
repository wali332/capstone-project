"""
VoiceGuard — Audio Processing & Spectrogram Pipeline
=====================================================
Full pipeline:
  1. Load audio (wav / mp3 / flac)
  2. Convert to mono
  3. Resample to standard rate
  4. Trim leading/trailing silence
  5. Noise reduction (spectral subtraction)
  6. Pre-emphasis filter (boost high frequencies)
  7. Normalize loudness (RMS normalization)
  8. Generate mel spectrogram
  9. Save spectrogram as PNG + numpy array

Usage:
  python scripts/audio_processor.py --input path/to/audio.wav
  python scripts/audio_processor.py --input path/to/audio.wav --output out/ --visualize
  python scripts/audio_processor.py --batch data/processed/real/ --output data/spectrograms/
"""

import argparse
import numpy as np
import librosa
import librosa.display
import soundfile as sf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path
from PIL import Image
import warnings
warnings.filterwarnings("ignore")

# ── Processing config ──────────────────────────────────────────────────────────
SAMPLE_RATE  = 22050
DURATION     = 4.0
N_MELS       = 128
N_FFT        = 2048
HOP_LENGTH   = 512
FMIN         = 50
FMAX         = 8000
IMG_SIZE     = 128
PRE_EMPHASIS = 0.97
NOISE_FRAMES = 10
TOP_DB       = 60


def load_audio(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    supported = {'.wav', '.mp3', '.flac', '.ogg', '.m4a'}
    if path.suffix.lower() not in supported:
        raise ValueError(f"Unsupported format: {path.suffix}")
    y, sr = librosa.load(str(path), sr=None, mono=False)
    return y, sr


def to_mono(y):
    if y.ndim > 1:
        return librosa.to_mono(y)
    return y


def resample(y, orig_sr, target_sr=SAMPLE_RATE):
    if orig_sr == target_sr:
        return y
    return librosa.resample(y, orig_sr=orig_sr, target_sr=target_sr)


def trim_silence(y, top_db=TOP_DB):
    y_trimmed, _ = librosa.effects.trim(y, top_db=top_db)
    if len(y_trimmed) < SAMPLE_RATE * 0.5:
        return y
    return y_trimmed


def reduce_noise(y, sr=SAMPLE_RATE):
    """
    Spectral subtraction noise reduction.
    Estimates noise from first N frames, subtracts it from every frame.
    Removes steady-state background noise without distorting speech.
    """
    D = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH)
    magnitude = np.abs(D)
    phase = np.angle(D)

    noise_estimate = np.mean(magnitude[:, :NOISE_FRAMES], axis=1, keepdims=True)

    alpha = 2.0  # over-subtraction factor
    beta  = 0.1  # spectral floor — prevents musical noise

    magnitude_clean = np.maximum(
        magnitude - alpha * noise_estimate,
        beta * noise_estimate
    )

    D_clean = magnitude_clean * np.exp(1j * phase)
    y_clean = librosa.istft(D_clean, hop_length=HOP_LENGTH)

    if len(y_clean) > len(y):
        y_clean = y_clean[:len(y)]
    elif len(y_clean) < len(y):
        y_clean = np.pad(y_clean, (0, len(y) - len(y_clean)))

    return y_clean


def apply_pre_emphasis(y, coeff=PRE_EMPHASIS):
    """
    Boosts high frequencies: y[n] = y[n] - coeff * y[n-1]
    Balances the spectrum so the CNN sees equal energy across frequencies.
    Helps detect subtle AI artifacts in upper frequency bands.
    """
    return np.append(y[0], y[1:] - coeff * y[:-1])


def normalize_rms(y, target_rms=0.1):
    """Normalize to target RMS — makes all clips equally loud."""
    rms = np.sqrt(np.mean(y ** 2))
    if rms < 1e-8:
        return y
    return y * (target_rms / rms)


def fix_duration(y, sr=SAMPLE_RATE, duration=DURATION):
    """Pad (repeat) or clip to exactly `duration` seconds."""
    target_len = int(sr * duration)
    if len(y) >= target_len:
        start = (len(y) - target_len) // 2
        return y[start:start + target_len]
    repeats = int(np.ceil(target_len / len(y)))
    return np.tile(y, repeats)[:target_len]


def generate_melspectrogram(y, sr=SAMPLE_RATE):
    """Generate mel spectrogram in dB scale."""
    mel = librosa.feature.melspectrogram(
        y=y, sr=sr,
        n_mels=N_MELS, n_fft=N_FFT, hop_length=HOP_LENGTH,
        fmin=FMIN, fmax=FMAX, power=2.0,
    )
    return librosa.power_to_db(mel, ref=np.max, top_db=80.0)


def spectrogram_to_array(mel_db, size=IMG_SIZE):
    """Resize spectrogram to square array normalized to [0, 1]."""
    img = Image.fromarray(mel_db).resize((size, size), Image.BILINEAR)
    arr = np.array(img, dtype=np.float32)
    return (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)


def process_audio(path, denoise=True, pre_emphasis=True):
    """Full pipeline. Returns dict with signal, spectrogram, metadata."""
    path = Path(path)
    y_raw, sr_orig = load_audio(path)
    y = to_mono(y_raw)
    y = resample(y, sr_orig, SAMPLE_RATE)
    sr = SAMPLE_RATE
    y = trim_silence(y)
    if denoise:
        y = reduce_noise(y, sr)
    if pre_emphasis:
        y = apply_pre_emphasis(y)
    y = normalize_rms(y)
    y = fix_duration(y, sr, DURATION)
    mel_db = generate_melspectrogram(y, sr)
    spec_array = spectrogram_to_array(mel_db, IMG_SIZE)
    duration_orig = librosa.get_duration(y=to_mono(y_raw), sr=sr_orig)
    return {
        "signal": y,
        "sample_rate": sr,
        "mel_db": mel_db,
        "spec_array": spec_array,
        "cnn_input": spec_array[..., np.newaxis],
        "duration": duration_orig,
        "original_sr": sr_orig,
        "filename": path.name,
    }


def save_spectrogram_png(spec_array, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray((spec_array * 255).astype(np.uint8))
    img.save(str(output_path))


def visualize_pipeline(path, output_dir=None):
    """Diagnostic visualization of every processing stage. Saves PNG."""
    path = Path(path)
    output_dir = Path(output_dir) if output_dir else path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    y_raw, sr_orig = load_audio(path)
    y_mono      = to_mono(y_raw)
    y_res       = resample(y_mono, sr_orig, SAMPLE_RATE)
    y_trimmed   = trim_silence(y_res)
    y_denoised  = reduce_noise(y_trimmed, SAMPLE_RATE)
    y_emph      = apply_pre_emphasis(y_denoised)
    y_norm      = normalize_rms(y_emph)
    y_final     = fix_duration(y_norm, SAMPLE_RATE, DURATION)
    mel_raw     = generate_melspectrogram(resample(y_mono, sr_orig, SAMPLE_RATE))
    mel_clean   = generate_melspectrogram(y_final)
    spec_final  = spectrogram_to_array(mel_clean, IMG_SIZE)

    fig = plt.figure(figsize=(18, 10), facecolor='#0D0D0F')
    fig.suptitle(f'VoiceGuard — Audio Processing Pipeline\n{path.name}',
                 color='white', fontsize=13, fontweight='bold', y=0.98)
    gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.55, wspace=0.35)

    title_cfg = {'color': 'white',   'fontsize': 9, 'fontweight': 'bold'}
    text_cfg  = {'color': '#aaaaaa', 'fontsize': 8}

    t_raw   = np.linspace(0, len(y_res)   / SAMPLE_RATE, len(y_res))
    t_clean = np.linspace(0, DURATION,                    len(y_final))

    # Waveforms
    ax0 = fig.add_subplot(gs[0, :2], facecolor='#141417')
    ax0.plot(t_raw, y_res, color='#6C63FF', linewidth=0.4, alpha=0.8)
    ax0.set_title('1. Raw waveform (mono + resample)', **title_cfg)
    ax0.set_xlabel('Time (s)', **text_cfg)
    ax0.tick_params(colors='#666')

    ax1 = fig.add_subplot(gs[0, 2:], facecolor='#141417')
    ax1.plot(t_clean, y_final, color='#00E5A0', linewidth=0.4, alpha=0.8)
    ax1.set_title('2. Processed waveform (denoised + normalized)', **title_cfg)
    ax1.set_xlabel('Time (s)', **text_cfg)
    ax1.tick_params(colors='#666')

    # Spectrograms
    ax2 = fig.add_subplot(gs[1, :2])
    img2 = librosa.display.specshow(
        mel_raw, sr=SAMPLE_RATE, hop_length=HOP_LENGTH,
        x_axis='time', y_axis='mel', fmin=FMIN, fmax=FMAX, ax=ax2, cmap='magma'
    )
    ax2.set_title('3. Raw mel spectrogram', **title_cfg)
    ax2.tick_params(colors='#666')
    fig.colorbar(img2, ax=ax2, format='%+2.0f dB').ax.tick_params(colors='#666')

    ax3 = fig.add_subplot(gs[1, 2:])
    img3 = librosa.display.specshow(
        mel_clean, sr=SAMPLE_RATE, hop_length=HOP_LENGTH,
        x_axis='time', y_axis='mel', fmin=FMIN, fmax=FMAX, ax=ax3, cmap='magma'
    )
    ax3.set_title('4. Clean mel spectrogram (full pipeline)', **title_cfg)
    ax3.tick_params(colors='#666')
    fig.colorbar(img3, ax=ax3, format='%+2.0f dB').ax.tick_params(colors='#666')

    # CNN input
    ax4 = fig.add_subplot(gs[2, :2])
    ax4.imshow(spec_final, aspect='auto', origin='lower', cmap='inferno', vmin=0, vmax=1)
    ax4.set_title(f'5. CNN input — {IMG_SIZE}x{IMG_SIZE} normalized', **title_cfg)
    ax4.set_xlabel('Time bins', **text_cfg)
    ax4.set_ylabel('Mel bins', **text_cfg)
    ax4.tick_params(colors='#666')
    ax4.set_facecolor('#141417')

    # Stats panel
    ax5 = fig.add_subplot(gs[2, 2:])
    ax5.axis('off')
    ax5.set_facecolor('#141417')
    ax5.set_title('Pipeline parameters', **title_cfg)

    duration_orig = librosa.get_duration(y=y_mono, sr=sr_orig)
    rms_raw   = np.sqrt(np.mean(y_res**2))
    rms_clean = np.sqrt(np.mean(y_final**2))
    db_change = 20 * np.log10((rms_clean + 1e-8) / (rms_raw + 1e-8))

    stats = [
        ('File',           path.name),
        ('Original SR',    f'{sr_orig:,} Hz'),
        ('Duration',       f'{duration_orig:.2f}s'),
        ('Target SR',      f'{SAMPLE_RATE:,} Hz'),
        ('Mel bins',       str(N_MELS)),
        ('FFT size',       str(N_FFT)),
        ('Hop length',     str(HOP_LENGTH)),
        ('Freq range',     f'{FMIN}-{FMAX} Hz'),
        ('Output shape',   f'({IMG_SIZE}, {IMG_SIZE}, 1)'),
        ('RMS raw',        f'{rms_raw:.4f}'),
        ('RMS clean',      f'{rms_clean:.4f}'),
        ('dB change',      f'{db_change:+.1f} dB'),
        ('Noise reduction','Spectral subtraction'),
        ('Filter',         f'Pre-emphasis a={PRE_EMPHASIS}'),
        ('Normalization',  'RMS target=0.1'),
    ]
    y_pos = 0.97
    for label, val in stats:
        ax5.text(0.02, y_pos, label + ':', color='#666666', fontsize=8,
                 transform=ax5.transAxes, va='top')
        ax5.text(0.48, y_pos, val, color='white', fontsize=8,
                 transform=ax5.transAxes, va='top')
        y_pos -= 0.065

    out_path = output_dir / f"{path.stem}_pipeline.png"
    plt.savefig(out_path, dpi=130, bbox_inches='tight', facecolor='#0D0D0F')
    plt.close()
    print(f"[✓] Visualization saved → {out_path}")
    return str(out_path)


def batch_process(input_dir, output_dir, label, max_files=None, denoise=True):
    from tqdm import tqdm
    input_dir  = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    exts  = {'.wav', '.mp3', '.flac', '.ogg'}
    files = [f for f in input_dir.iterdir() if f.suffix.lower() in exts]
    if max_files:
        files = files[:max_files]
    X, y_labels = [], []
    failed = 0
    for f in tqdm(files, desc=f"{'real' if label==0 else 'fake'}"):
        try:
            result = process_audio(f, denoise=denoise)
            X.append(result['spec_array'])
            y_labels.append(label)
            save_spectrogram_png(result['spec_array'], output_dir / f"{f.stem}.png")
        except Exception as e:
            failed += 1
            if failed <= 5:
                print(f"  [!] Skipped {f.name}: {e}")
    print(f"  Processed: {len(X)}, Failed: {failed}")
    return X, y_labels


def main():
    parser = argparse.ArgumentParser(description='VoiceGuard audio processor')
    parser.add_argument('--input',      type=str, help='Single audio file')
    parser.add_argument('--batch',      type=str, help='Folder of audio files')
    parser.add_argument('--output',     type=str, default='output/')
    parser.add_argument('--visualize',  action='store_true')
    parser.add_argument('--no-denoise', action='store_true')
    args = parser.parse_args()

    if args.input:
        path = Path(args.input)
        print(f"\n[→] Processing: {path.name}")
        result = process_audio(path, denoise=not args.no_denoise)
        print(f"  Original SR   : {result['original_sr']:,} Hz")
        print(f"  Duration      : {result['duration']:.2f}s")
        print(f"  Spectrogram   : {result['spec_array'].shape}")
        print(f"  CNN input     : {result['cnn_input'].shape}")
        print(f"  Value range   : [{result['spec_array'].min():.3f}, {result['spec_array'].max():.3f}]")

        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)

        png_out = out_dir / f"{path.stem}_spectrogram.png"
        save_spectrogram_png(result['spec_array'], png_out)
        print(f"\n[✓] Spectrogram PNG → {png_out}")

        npy_out = out_dir / f"{path.stem}_array.npy"
        np.save(str(npy_out), result['spec_array'])
        print(f"[✓] Numpy array    → {npy_out}")

        if args.visualize:
            visualize_pipeline(path, out_dir)

    elif args.batch:
        folder = Path(args.batch)
        print(f"\n[→] Batch processing: {folder}")
        X, y = batch_process(folder, Path(args.output), label=0,
                              denoise=not args.no_denoise)
        print(f"\n[✓] Done — {len(X)} files processed.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
