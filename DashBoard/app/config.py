"""
Configuration Constants
=======================
Centralized configuration for colors, metrics, and display labels.
Imported across layout and callbacks to maintain consistency.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# CONTINENT COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════════════
# Consistent across all charts to help viewers quickly identify regions
CONTINENT_COLORS = {
    "Asia":          "#185FA5",     # Deep Blue
    "Europe":        "#A32D2D",     # Deep Red
    "Africa":        "#3B6D11",     # Dark Green
    "North America": "#BA7517",     # Orange-Brown
    "South America": "#534AB7",     # Purple
    "Oceania":       "#1D9E75",     # Teal
}

# ═══════════════════════════════════════════════════════════════════════════════
# CONTINENT LIST
# ═══════════════════════════════════════════════════════════════════════════════
CONTINENT_OPTIONS = [
    "Asia", "Europe", "Africa", "North America", "South America", "Oceania"
]

# ═══════════════════════════════════════════════════════════════════════════════
# METRIC DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════
# Available metrics for analysis, with column names and display labels

METRIC_OPTIONS = [
    {"label": "إجمالي الإصابات",   "value": "total_cases"},
    {"label": "إجمالي الوفيات",    "value": "total_deaths"},
    {"label": "إجمالي التطعيمات",  "value": "total_vaccinations"},
    {"label": "إصابات / مليون",    "value": "cases_per_million"},
    {"label": "وفيات / مليون",     "value": "deaths_per_million"},
    {"label": "معدل الوفيات %",    "value": "case_fatality_rate"},
    {"label": "نسبة التطعيم %",    "value": "vaccination_rate_pct"},
    {"label": "GDP للفرد",         "value": "gdp_per_capita"},
]

METRIC_LABELS = {
    "total_cases":          "إجمالي الإصابات",
    "total_deaths":         "إجمالي الوفيات",
    "total_vaccinations":   "إجمالي التطعيمات",
    "cases_per_million":    "إصابات / مليون",
    "deaths_per_million":   "وفيات / مليون",
    "case_fatality_rate":   "معدل الوفيات %",
    "vaccination_rate_pct": "نسبة التطعيم %",
    "gdp_per_capita":       "GDP للفرد",
}

# ═══════════════════════════════════════════════════════════════════════════════
# CHART LAYOUT DEFAULTS
# ═══════════════════════════════════════════════════════════════════════════════
# Consistent styling applied to all Plotly charts

CHART_LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=10, r=10, t=50, b=30),
    font=dict(family="'Segoe UI', sans-serif", size=11),
    hovermode="closest",
)

# ═══════════════════════════════════════════════════════════════════════════════
# UI STYLING CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
# Font sizes, margins, and spacing for consistent UI appearance

FONT_SIZES = {
    "header_h1":     "1.9rem",
    "section_h4":    "1.1rem",
    "label":         "0.9rem",
    "body":          "0.9rem",
    "small":         "0.85rem",
    "tiny":          "0.75rem",
}

SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "12px",
    "lg": "16px",
    "xl": "24px",
}

BORDER_RADIUS = {
    "sm": "8px",
    "md": "10px",
    "lg": "12px",
}

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER STYLING
# ═══════════════════════════════════════════════════════════════════════════════

HEADER_STYLE = {
    "background": "linear-gradient(135deg, #0d2137 0%, #1a3c5e 60%, #185FA5 100%)",
    "padding": "28px 40px 22px",
    "color": "white",
    "boxShadow": "0 4px 20px rgba(0,0,0,0.25)",
}

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDER & CONTROL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

TOP_N_SLIDER = {
    "min": 5,
    "max": 50,
    "step": 5,
    "default": 15,
}

VIEW_OPTIONS = [
    {"label": " قيمة مطلقة", "value": "raw"},
    {"label": " لكل مليون",  "value": "per_million"},
    {"label": " نسبة %",     "value": "pct"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# DATA PROCESSING SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

# Columns to keep when loading CSV data
REQUIRED_COLUMNS = [
    "location", "continent", "population",
    "total_cases", "total_deaths", "total_vaccinations",
    "cases_per_million", "deaths_per_million",
    "case_fatality_rate", "vaccination_rate_pct",
    "gdp_per_capita", "median_age", "population_density",
    "life_expectancy", "human_development_index",
]

# ═══════════════════════════════════════════════════════════════════════════════
# STACKED METRICS FOR COMPARISON CHARTS
# ═══════════════════════════════════════════════════════════════════════════════

STACK_METRICS = {
    "إصابات": "total_cases",
    "وفيات": "total_deaths",
    "تطعيمات": "total_vaccinations",
}

# Stack colors (use subset of CONTINENT_COLORS for consistency)
STACK_COLORS = ["#185FA5", "#A32D2D", "#3B6D11", "#BA7517"]

# ═══════════════════════════════════════════════════════════════════════════════
# HISTOGRAM CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

HISTOGRAM_BINS = 25
HISTOGRAM_COLOR = "#185FA5"

# ═══════════════════════════════════════════════════════════════════════════════
# BUBBLE CHART CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

BUBBLE_SIZE_MAX = 55
BUBBLE_OPACITY = 0.72

# ═══════════════════════════════════════════════════════════════════════════════
# SCATTER PLOT CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

SCATTER_MARKER_SIZE = 8
SCATTER_OPACITY = 0.72

# ═══════════════════════════════════════════════════════════════════════════════
# TIME-SERIES MOVING AVERAGE
# ═══════════════════════════════════════════════════════════════════════════════

MOVING_AVERAGE_WINDOW = 7  # 7-day moving average

# ═══════════════════════════════════════════════════════════════════════════════
# DATA TABLE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

TABLE_COLUMNS_DISPLAY = {
    "location": "الدولة",
    "continent": "القارة",
    "total_cases": "الإصابات",
    "total_deaths": "الوفيات",
    "cases_per_million": "إصابات/مليون",
    "deaths_per_million": "وفيات/مليون",
    "case_fatality_rate": "CFR %",
    "vaccination_rate_pct": "تطعيم %",
    "gdp_per_capita": "GDP/فرد",
    "population": "السكان",
}

TABLE_PAGE_SIZE = 15

# ═══════════════════════════════════════════════════════════════════════════════
# DEFAULT DATA PATH
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_CSV_PATH = "./data/owid_covid_cleaned.csv"
