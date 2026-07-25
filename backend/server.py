"""
PRISM Voice Assistant — FastAPI Server Entry Point
Starts the uvicorn server that serves the React frontend's HTTP requests.
Run directly: python -m backend.server
or via Electron: spawned as a child process
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )
