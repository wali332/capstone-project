# VoiceGuard - Frontend + Backend Integration Setup

This document provides step-by-step instructions to set up and run the VoiceGuard application with both frontend and backend.

## Project Structure

```
capstone/
├── src/                          # React frontend (Vite)
│   ├── api/
│   │   └── api.js               # Backend API client
│   ├── components/
│   │   ├── LiveDemo.jsx         # Main demo component (updated)
│   │   └── ...
│   └── main.jsx
│
├── voiceguard-backend/           # Python FastAPI backend
│   ├── app.py                   # Main API server
│   ├── run.py                   # Server runner
│   ├── requirements.txt          # Python dependencies
│   ├── scripts/
│   │   ├── audio_pipeline.py    # Audio processing
│   │   ├── audio_processor.py   # Audio utilities
│   │   ├── train.py             # Model training
│   │   └── ...
│   └── models/
│       └── voiceguard_model.h5  # Pre-trained ML model
│
├── package.json                  # Frontend dependencies
├── .env.local                    # Environment variables
└── vite.config.js               # Vite configuration
```

## Prerequisites

### System Requirements

- **Node.js**: v18+ ([Download](https://nodejs.org/))
- **Python**: 3.9+ ([Download](https://www.python.org/))
- **Git**: Latest stable version

### Verify Installation

```bash
# Check Node.js
node --version
npm --version

# Check Python
python --version
```

## Backend Setup

### Step 1: Navigate to Backend Directory

```bash
cd voiceguard-backend
```

### Step 2: Create Python Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

If you need audio-specific packages (optional):
```bash
pip install -r requirements-audio.txt
```

### Step 4: Download/Train ML Model

The backend requires a trained model. Two options:

**Option A: Use pre-trained model** (if available)
```bash
# If model exists at voiceguard-backend/models/voiceguard_model.h5, skip to next step
```

**Option B: Train a new model**
```bash
python scripts/train.py
```

### Step 5: Start Backend Server

```bash
python run.py
```

Or directly:
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Started server process [XXXX]
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
INFO:     [✓] Model loaded and ready
```

**API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

## Frontend Setup

### Step 1: Navigate to Frontend Directory

From the project root:
```bash
# Make sure you're not in voiceguard-backend
cd ../
```

### Step 2: Install Node Dependencies

```bash
npm install
```

### Step 3: Environment Configuration

The `.env.local` file should already exist with:
```
VITE_API_URL=http://localhost:8000
```

If it doesn't exist, create it in the project root:
```bash
echo VITE_API_URL=http://localhost:8000 > .env.local
```

### Step 4: Start Development Server

```bash
npm run dev
```

**Expected Output:**
```
  VITE v8.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

## Running the Full Application

### Terminal 1: Backend

```bash
cd voiceguard-backend
# Activate venv (if not already activated)
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Start server
python run.py
# Server runs on http://localhost:8000
```

### Terminal 2: Frontend

```bash
# From project root
npm run dev
# Frontend runs on http://localhost:5173
```

### Terminal 3 (Optional): Development Tools

```bash
# Lint check
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

## Testing the Integration

1. **Open Browser:** http://localhost:5173
2. **Navigate to:** "Try it yourself" section
3. **Upload Audio File:**
   - Drag and drop a `.wav`, `.mp3`, or `.flac` file
   - Or click "or browse files" button
4. **View Results:**
   - See terminal animation logs
   - Check verdict: "AI GENERATED" or "HUMAN VOICE"
   - View confidence percentage and audio stats

## API Endpoints

All endpoints are accessible at `http://localhost:8000`

### GET `/`
Returns basic service info
```bash
curl http://localhost:8000/
```

### GET `/health`
Check if backend is running and model is loaded
```bash
curl http://localhost:8000/health
```

### POST `/analyze`
Main endpoint - analyze audio file
```bash
curl -X POST -F "file=@audio.wav" http://localhost:8000/analyze
```

**Response (JSON):**
```json
{
  "verdict": "HUMAN VOICE",
  "fake_percent": 25,
  "real_percent": 75,
  "confidence": 75,
  "sample_rate": "48.0 kHz",
  "duration": "00:02:14"
}
```

## Troubleshooting

### Issue: "Backend API is not running"
**Solution:** Make sure the backend server is running on `http://localhost:8000`
```bash
# Check if port 8000 is in use
# Windows:
netstat -ano | findstr :8000

# macOS/Linux:
lsof -i :8000
```

### Issue: "Model not loaded"
**Solution:** Train or download the model
```bash
cd voiceguard-backend
python scripts/train.py
```

### Issue: "Unsupported file type"
**Solution:** Only `.wav`, `.mp3`, and `.flac` are supported
- Ensure your audio file has the correct extension
- File should not be corrupted

### Issue: CORS errors in browser console
**Solution:** This should be automatically handled. If persists:
- Verify backend is running on port 8000
- Check that CORS middleware is enabled in `app.py`

### Issue: File upload fails with 503 error
**Solution:** Model is not loaded
```bash
# In backend terminal
python scripts/train.py
# Then restart backend
python run.py
```

### Issue: Network timeout errors
**Solution:** Backend is too slow or audio file is too large
- Try with a smaller audio file (< 10 MB)
- Check system resources (CPU, RAM)
- Ensure model inference isn't taking too long

## Environment Variables

Create/modify `.env.local` to customize:

```bash
# Backend API URL (default: http://localhost:8000)
VITE_API_URL=http://localhost:8000

# For production deployment
# VITE_API_URL=https://api.example.com
```

## Supported Audio Formats

- **WAV** (.wav) - Uncompressed, recommended
- **MP3** (.mp3) - Compressed
- **FLAC** (.flac) - Lossless compression

**Requirements:**
- Sample rate: Any (will be normalized)
- Duration: Minimum ~2 seconds recommended
- File size: Up to 100 MB

## API Integration Code

The frontend communicates with the backend using the API client in `src/api/api.js`:

```javascript
import { uploadAudio, validateAudioFile, checkHealth } from './api/api';

// Upload and analyze audio
const result = await uploadAudio(audioFile);
// Returns: { verdict, fake_percent, real_percent, confidence, sample_rate, duration }

// Validate before upload
const validation = validateAudioFile(file);
// Returns: { valid: boolean, error?: string }

// Check backend status
const status = await checkHealth();
// Returns: { status, model_ready }
```

## Building for Production

### Build Frontend

```bash
npm run build
```

Creates optimized build in `dist/` directory.

### Deploy Backend

1. Ensure model file is included: `voiceguard-backend/models/voiceguard_model.h5`
2. Install production dependencies: `pip install -r requirements.txt`
3. Run with production server:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:app"
```

4. Update `.env.local` with production API URL:
```bash
VITE_API_URL=https://your-api.example.com
```

## Architecture Overview

```
┌─────────────────────┐
│   React Frontend    │
│   (Vite, Port 5173) │
└──────────┬──────────┘
           │ HTTP Fetch
           │ /analyze endpoint
           ↓
┌─────────────────────────────┐
│   FastAPI Backend           │
│   (Uvicorn, Port 8000)      │
│                             │
│  ├─ CORS Middleware         │
│  ├─ File Upload Handler     │
│  ├─ Audio Pipeline          │
│  └─ ML Model Inference      │
└─────────────────────────────┘
           │
           ↓
    ┌─────────────┐
    │  ML Model   │
    │ (TensorFlow)│
    └─────────────┘
```

## Performance Tips

1. **Audio Quality:** Lower sample rate = faster processing
2. **Backend Resources:** More CPU cores = faster inference
3. **File Size:** Smaller files are processed faster
4. **Model Optimization:** Consider quantization for production

## Support & Documentation

- **FastAPI Docs:** http://localhost:8000/docs
- **Vite Docs:** https://vitejs.dev/
- **React Docs:** https://react.dev/
- **TensorFlow:** https://tensorflow.org/

## Next Steps

- [ ] Train/download ML model
- [ ] Start backend server
- [ ] Start frontend development server
- [ ] Test with sample audio files
- [ ] Deploy to production

---

**Last Updated:** April 2024
**Version:** 1.0.0
