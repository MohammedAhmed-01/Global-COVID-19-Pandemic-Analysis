#!/usr/bin/env python3
"""
Entry point script for running the COVID-19 Dashboard from project root.

This script properly handles imports and starts the Dash server.
"""
import sys
from pathlib import Path

# Add the StreamlitDashBoard directory to Python path
streamlit_dashboard_path = Path(__file__).parent / "StreamlitDashBoard"
sys.path.insert(0, str(streamlit_dashboard_path))

# Now import and run the app
from app.app import app, server

if __name__ == "__main__":
    print("🦠 Starting COVID-19 Global Pandemic Analysis Dashboard...")
    print("📊 Open your browser and navigate to: http://127.0.0.1:8050/")
    app.run(debug=True, host="127.0.0.1", port=8050)
