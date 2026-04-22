"""
VoiceGuard — Server entry point
Run this file to start the API: python main.py
"""
import uvicorn
from app import app   # noqa: F401 — imported for uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
