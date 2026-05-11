"""
COVID-19 Global Pandemic Analysis Dashboard

This is the main entry point for the interactive Plotly Dash dashboard.

The dashboard provides:
- Interactive visualization of COVID-19 pandemic data
- Multiple chart types covering comparison, relationship, and distribution analysis
- Real-time filtering and data exploration
- CSV export functionality

Quick Start:
    python app.py
    Then open http://127.0.0.1:8050/

Dataset: Our World in Data — COVID-19 (owid-covid-data.csv)
"""

from dash import Dash
import dash_bootstrap_components as dbc

# Import layout and callback registration using relative imports
from .layout.dashboard_layout import build_layout
from .callbacks.dashboard_callbacks import register_callbacks

# Initialize Dash application with Bootstrap theme for professional styling
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="🦠 COVID-19 Global Dashboard",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

# Expose Flask server for production deployment (e.g., gunicorn, Heroku)
server = app.server

# Build the dashboard layout and register all interactive callbacks
app.layout = build_layout()
register_callbacks(app)


if __name__ == "__main__":
    # Run development server with hot reload enabled
    app.run(debug=True, host="127.0.0.1", port=8050)
