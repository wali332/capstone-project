# VoiceGuard Quick Reference

## Quick Start (3 Commands)

**Terminal 1 - Backend:**
```bash
cd voiceguard-backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python run.py
```

**Terminal 2 - Frontend:**
```bash
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend (Vite) | 5173 | http://localhost:5173 |
| Backend (FastAPI) | 8000 | http://localhost:8000 |
| Backend Docs | 8000 | http://localhost:8000/docs |

## Key Files

| File | Purpose |
|------|---------|
| `src/api/api.js` | Frontend API client |
| `src/components/LiveDemo.jsx` | Main UI component |
| `voiceguard-backend/app.py` | Backend API server |
| `.env.local` | Environment variables |
| `INTEGRATION_SETUP.md` | Full setup guide |

## Common Commands

```bash
# Backend
cd voiceguard-backend
pip install -r requirements.txt      # Install dependencies
python run.py                        # Start server
python scripts/train.py              # Train model
python -m uvicorn app:app --reload  # Dev server with reload

# Frontend  
npm install                          # Install dependencies
npm run dev                          # Start dev server
npm run build                        # Production build
npm run lint                         # Check code
npm run preview                      # Preview production build
```

## API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Analyze audio
curl -X POST -F "file=@audio.wav" http://localhost:8000/analyze

# API documentation (interactive)
# Open: http://localhost:8000/docs
```

## Frontend API Usage

```javascript
import { uploadAudio, validateAudioFile } from './api/api';

// Validate
const validation = validateAudioFile(file);
if (!validation.valid) {
  console.error(validation.error);
  return;
}

// Upload
try {
  const result = await uploadAudio(file);
  console.log(result.verdict); // "AI GENERATED" or "HUMAN VOICE"
  console.log(result.confidence); // 0-100
} catch (error) {
  console.error('Upload failed:', error);
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | Kill process: `lsof -ti:8000 \| xargs kill -9` |
| Model not loaded | Run: `python scripts/train.py` |
| Backend not responding | Check firewall, restart server |
| CORS errors | Ensure backend is at `http://localhost:8000` |
| File upload fails | Check file format (.wav, .mp3, .flac) |

## Environment Variables

Create `.env.local`:
```bash
VITE_API_URL=http://localhost:8000
```

For production:
```bash
VITE_API_URL=https://api.yoursite.com
```

## Project Structure

```
capstone/
├── src/
│   ├── api/api.js                    ← API client
│   ├── components/LiveDemo.jsx       ← UI component (updated)
│   ├── App.jsx
│   └── ...
├── voiceguard-backend/
│   ├── app.py                        ← FastAPI server
│   ├── run.py
│   ├── requirements.txt
│   └── scripts/
│       ├── audio_pipeline.py
│       ├── train.py
│       └── ...
├── .env.local                        ← Config (new)
├── INTEGRATION_SETUP.md              ← Full guide (new)
├── package.json
├── vite.config.js
└── README.md
```

## Testing

1. **Start both servers** (as shown in Quick Start)
2. **Open** http://localhost:5173
3. **Upload audio** via drag-drop or file browser
4. **Wait for analysis** (animation shows progress)
5. **View results** (verdict + confidence %)

## Architecture

```
React App (5173)
      ↓
  Fetch /analyze
      ↓
FastAPI Server (8000)
      ↓
Audio Processing
      ↓
ML Model Inference
      ↓
Return JSON Result
      ↓
Update UI
```

## Model Training

```bash
cd voiceguard-backend
python scripts/train.py
# Creates: models/voiceguard_model.h5
```

## Production Build

```bash
# Frontend
npm run build
# Creates: dist/

# Backend (with gunicorn)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:app"
```

## Support Files

- **Setup Guide:** `INTEGRATION_SETUP.md`
- **API Client:** `src/api/api.js`
- **Component:** `src/components/LiveDemo.jsx`
- **Config:** `.env.local`

---

**For detailed setup:** See `INTEGRATION_SETUP.md`
