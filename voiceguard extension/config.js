/**
 * VoiceGuard extension configuration.
 * Mirrors web app default: VITE_API_URL || http://localhost:8000
 */
const VOICEGUARD_CONFIG = {
  API_URL: "http://localhost:8000",
  /** Match backend audio_pipeline.py DURATION (4.0 seconds). */
  RECORD_DURATION_SEC: 4,
};
