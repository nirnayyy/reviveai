import os
import sys

# Ensure repository root is on sys.path for serverless resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app

# Expose app instance for Vercel ASGI runner
handler = app
