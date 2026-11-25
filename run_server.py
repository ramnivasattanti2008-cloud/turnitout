"""
One-click Web Application Launcher for TextHumanizer Pro.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import HOST, PORT
from web.app import app

if __name__ == "__main__":
    print("=" * 60)
    print("TextHumanizer Pro - 100% Anti-AI & Plagiarism Remover")
    print(f"Server active at: http://{HOST}:{PORT}")
    print("Open this URL in your web browser to start humanizing text!")
    print("=" * 60)
    app.run(host=HOST, port=PORT, debug=False)
