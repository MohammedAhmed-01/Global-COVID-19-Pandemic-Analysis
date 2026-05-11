"""
Utility Functions
=================
Shared helper functions used across layout and callbacks.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from .config import CHART_LAYOUT


def format_number(value):
    """
    Format numbers for human-readable display.
    
    Examples: 1500000 → "1.5M", 45000 → "45K", 123 → "123"
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    
    v = float(value)
    if v >= 1e9:
        return f"{v/1e9:.2f}B"
    if v >= 1e6:
        return f"{v/1e6:.2f}M"
    if v >= 1e3:
        return f"{v/1e3:.0f}K"
    return f"{v:.1f}"


def create_empty_figure(message="لا تتوفر بيانات كافية"):
    """
    Create an empty figure with a message.
    
    Used when data is unavailable or filters return no results.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        showarrow=False,
        font=dict(size=14, color="#aaa"),
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5
    )
    fig.update_layout(**CHART_LAYOUT, height=380)
    return fig


def load_csv(path):
    """Load CSV file with error handling."""
    try:
        df = pd.read_csv(path, low_memory=False)
        return df
    except Exception as e:
        raise ValueError(f"Failed to load CSV: {str(e)}")


def ensure_numeric_columns(df, columns):
    """Convert specified columns to numeric type."""
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def get_display_values(df, metric, view):
    """
    Get display values based on view type.
    
    Supports:
    - 'raw': absolute values
    - 'per_million': per-million normalization
    - 'pct': percentage of population
    """
    if metric not in df.columns:
        return pd.Series(0, index=df.index)
    
    base = df[metric].fillna(0)
    
    if view == "per_million" and "population" in df.columns:
        pop = df["population"].replace(0, np.nan)
        return base / pop * 1e6
    
    if view == "pct" and "population" in df.columns:
        pop = df["population"].replace(0, np.nan)
        return base / pop * 100
    
    return base


def filter_by_continent(df, continents):
    """Filter dataframe to selected continents."""
    if not continents or not isinstance(continents, list):
        return df
    return df[df["continent"].isin(continents)]


def get_top_n(df, column, n=15):
    """Get top-N entries by column value."""
    return df.nlargest(n, column)


def rename_columns_for_display(df, rename_map):
    """Rename columns using provided mapping."""
    return df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})


def process_date_column(df, column="date"):
    """Parse and ensure date column is datetime type."""
    if column in df.columns:
        df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def calculate_moving_average(series, window=7):
    """Calculate moving average for smoothing trends."""
    return series.rolling(window=window, center=True).mean()


def remove_zero_values(series):
    """Replace zero values with NaN for cleaner visualization."""
    return series.replace(0, np.nan)


def validate_data_not_empty(df):
    """Check if dataframe has usable data."""
    return len(df) > 0 and not df.empty
