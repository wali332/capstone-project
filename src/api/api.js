/**
 * VoiceGuard API Client
 * Handles all communication with the Python FastAPI backend
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Upload audio file to backend for analysis
 * @param {File} audioFile - Audio file to analyze
 * @returns {Promise<Object>} Analysis result with verdict and confidence
 */
export async function uploadAudio(audioFile) {
  try {
    const formData = new FormData();
    formData.append('file', audioFile);

    const response = await fetch(`${API_URL}/analyze`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail ||
        `API Error: ${response.status} ${response.statusText}`
      );
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Upload error:', error);
    throw error;
  }
}

/**
 * Check backend health status
 * @returns {Promise<Object>} Health status
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_URL}/health`);
    if (!response.ok) throw new Error('Health check failed');
    return await response.json();
  } catch (error) {
    console.error('Health check error:', error);
    throw error;
  }
}

/**
 * Format file size in human-readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Validate audio file before upload
 * @param {File} file - File to validate
 * @returns {Object} Validation result {valid: boolean, error?: string}
 */
export function validateAudioFile(file) {
  const ALLOWED_TYPES = ['audio/wav', 'audio/wave', 'audio/x-wav', 
                         'audio/mpeg', 'audio/mp3',
                         'audio/flac', 'audio/x-flac'];
  const ALLOWED_EXTENSIONS = ['.wav', '.mp3', '.flac'];
  const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

  const fileName = file.name.toLowerCase();
  const fileExt = fileName.substring(fileName.lastIndexOf('.'));

  if (!ALLOWED_EXTENSIONS.includes(fileExt) && !ALLOWED_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: 'Only .wav, .mp3, and .flac files are supported',
    };
  }

  if (file.size > MAX_FILE_SIZE) {
    return {
      valid: false,
      error: `File size exceeds 100MB limit (${formatFileSize(file.size)})`,
    };
  }

  if (file.size === 0) {
    return {
      valid: false,
      error: 'File is empty',
    };
  }

  return { valid: true };
}
