"""
MiroFish Demo Backend — Lightweight mock Flask server.

Serves realistic, pre-built demo data for all frontend endpoints so the app
can run without the heavy camel-ai / PyTorch production backend.  Total
image size drops from ~5.8 GB to ~150 MB.

Routes are organized into Flask Blueprints under app/api/demo/.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (one level up from backend/)
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
load_dotenv(override=True)

# Add backend/ to sys.path for llm_client, and app/api/ for the demo package.
# Importing as "from demo import ..." avoids loading the production app/__init__.py.
_backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _backend_dir)
sys.path.insert(0, os.path.join(_backend_dir, "app", "api"))

from flask import Flask
from flask_cors import CORS

from demo import register_demo_blueprints

app = Flask(__name__)
CORS(app)
register_demo_blueprints(app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"MiroFish Demo Backend starting on port {port} (demo mode)")
    app.run(host="0.0.0.0", port=port, debug=debug)
