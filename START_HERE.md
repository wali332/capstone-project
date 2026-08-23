# 🚀 VoiceGuard - Start Here!

## 1️⃣ Quick Start (Copy & Paste)

### Terminal 1: Backend

```bash
cd voiceguard-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

**Expected Output:**
```
[→] Loading model from ...
[✓] Model loaded and ready
INFO: Started server process
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2: Frontend

```bash
npm install
npm run dev
```

**Expected Output:**
```
➜  Local:   http://localhost:5173/
```

## 2️⃣ Test It!

1. Open **http://localhost:5173** in your browser
2. Scroll to **"Try it yourself"** section
3. **Drag & drop** an audio file (`.wav`, `.mp3`, `.flac`)
4. **Watch** the animation
5. **See results** - Real verdict from AI model!

---

## 📁 What Was Done?

### ✅ Backend (Already Ready)
- FastAPI server with `/analyze` endpoint
- CORS enabled ✓
- Model inference ready ✓

### ✅ Frontend API Layer (NEW)
**File:** `src/api/api.js`
- Upload audio to backend
- Handle errors gracefully
- Validate files before upload
- Format responses

### ✅ React Component (UPDATED)
**File:** `src/components/LiveDemo.jsx`
- Now calls real backend API
- Shows real results (not mock data)
- Better error handling
- User-friendly error messages

### ✅ Configuration (NEW)
**File:** `.env.local`
- Backend API URL
- Easy to change for production

### ✅ Documentation (NEW)
- `INTEGRATION_SETUP.md` - Full setup guide
- `QUICK_REFERENCE.md` - Commands reference
- `CHANGES_SUMMARY.md` - What changed

---

## 🔧 If Backend Doesn't Work

### Check Python
```bash
python --version  # Should be 3.9+
```

### Check Port 8000
```bash
# Windows - see what's using port 8000
netstat -ano | findstr :8000

# macOS/Linux
lsof -i :8000
```

### Download Model
If model not found:
```bash
cd voiceguard-backend
python scripts/train.py  # Takes ~5-10 minutes
```

---

## 🌐 API Endpoints

```bash
# Check if running
curl http://localhost:8000/health

# Interactive API docs
http://localhost:8000/docs

# Upload audio (test)
curl -X POST -F "file=@audio.wav" http://localhost:8000/analyze
```

---

## 📂 Project Structure

```
capstone/
├── src/
│   ├── api/api.js              ← NEW: API client
│   ├── components/
│   │   └── LiveDemo.jsx        ← UPDATED: Real API calls
│   └── ...
├── voiceguard-backend/
│   ├── app.py                  ← FastAPI server
│   ├── requirements.txt
│   └── scripts/
│       ├── audio_pipeline.py   ← Audio processing
│       └── train.py            ← Model training
├── .env.local                  ← NEW: Config
├── INTEGRATION_SETUP.md        ← NEW: Full setup
├── QUICK_REFERENCE.md          ← NEW: Quick commands
└── CHANGES_SUMMARY.md          ← NEW: What changed
```

---

## 🎯 How It Works

```
User uploads audio
        ↓
Frontend validates file
        ↓
Sends to: POST /analyze
        ↓
Backend processes audio:
  - Load audio bytes
  - Extract mel spectrogram
  - Run ML model inference
        ↓
Returns JSON:
  {
    "verdict": "HUMAN VOICE",
    "fake_percent": 25,
    "real_percent": 75,
    "confidence": 75,
    ...
  }
        ↓
Frontend displays results
```

---

## ⚙️ Configuration

Change API URL in `.env.local`:

```bash
# Development (default)
VITE_API_URL=http://localhost:8000

# Production example
VITE_API_URL=https://api.voiceguard.com
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Backend API is not running" | Start backend: `python run.py` |
| Port 8000 in use | Kill process or restart OS |
| Model not found | Run: `python scripts/train.py` |
| File upload fails | Use .wav, .mp3, or .flac format |
| CORS error in console | Backend should be at http://localhost:8000 |

---

## 📖 Full Guides

- **Complete Setup:** See `INTEGRATION_SETUP.md`
- **Quick Commands:** See `QUICK_REFERENCE.md`
- **All Changes:** See `CHANGES_SUMMARY.md`

---

## ✨ Key Features Implemented

✅ **Real API Integration**
- Frontend uploads to backend
- Backend processes audio
- ML model provides verdict

✅ **Error Handling**
- File validation
- Backend connectivity checks
- User-friendly error messages

✅ **Environment Configuration**
- Easy to switch development/production
- Uses Vite environment variables

✅ **No Breaking Changes**
- Existing UI kept intact
- Animations still work
- Clean code structure

---

## 🚢 Next Steps

1. ✅ Start both servers (see Quick Start)
2. ✅ Test with audio file
3. 🔜 Deploy to production (see `INTEGRATION_SETUP.md`)
4. 🔜 Monitor performance
5. 🔜 Optimize as needed

---

## 📞 Need Help?

1. Check troubleshooting above
2. See `QUICK_REFERENCE.md` for all commands
3. See `INTEGRATION_SETUP.md` for detailed setup
4. Check http://localhost:8000/docs for API docs
5. Look at browser console for errors

---

**Ready?** Start with Terminal 1 command above! 🎉

