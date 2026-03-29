"""
SpectrumIA - Streamlit Cloud Entry Point

This file serves as the entry point for Streamlit Cloud deployment.
It imports and runs the main application from app/main.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the main app
from app.main import *  # noqa: F401, F403
