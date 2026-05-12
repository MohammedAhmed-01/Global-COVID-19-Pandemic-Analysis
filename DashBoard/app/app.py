"""
COVID-19 Global Pandemic Analysis Dashboard
============================================
Main entry point — run with:  python app.py
Then open:  http://127.0.0.1:8050/

Team Member 5 — Dashboard Development & Documentation
Dataset : Our World in Data — COVID-19  (owid-covid-data.csv)
"""

import os
import sys
from pathlib import Path

# Ensure the parent directory (DashBoard) is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dash import Dash
import dash_bootstrap_components as dbc

# ── Internal modules ───────────────────────────────────────────────────────────
from app.layout.dashboard_layout import build_layout
from app.callbacks.dashboard_callbacks import register_callbacks

# ══════════════════════════════════════════════════════════════════════════════
# APP INITIALISATION
# ══════════════════════════════════════════════════════════════════════════════
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="🦠 COVID-19 Global Dashboard",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server          # expose Flask server for deployment

# ── Layout & Callbacks ─────────────────────────────────────────────────────────
app.layout = build_layout()
register_callbacks(app)

# ══════════════════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
