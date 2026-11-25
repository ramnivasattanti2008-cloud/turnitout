"""
Vercel Serverless Function entrypoint for Turnitout (TextHumanizer Pro).
Routes all incoming HTTP requests to the WSGI Flask application.
"""
import os
import sys
from pathlib import Path

# Add project root to sys.path so core, web, config are discoverable
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from web.app import app

# Vercel looks for the WSGI application variable 'app'
__all__ = ["app"]
