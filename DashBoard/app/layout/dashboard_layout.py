"""
Dashboard Layout
================
Defines the complete Plotly Dash layout for the COVID-19 pandemic dashboard.

The layout is organized into logical sections:
- Header with KPI summary cards
- Interactive control panel with filters
- 9 chart sections (one per week of course requirements)
- Data table with search and export functionality

All colors and constants are imported from config.py for consistency.
"""

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

# Import centralized configuration
from app.config import (
    CONTINENT_COLORS, CONTINENT_OPTIONS, METRIC_OPTIONS,
    FONT_SIZES, SPACING, BORDER_RADIUS, HEADER_STYLE,
    TOP_N_SLIDER, VIEW_OPTIONS, TABLE_COLUMNS_DISPLAY,
    TABLE_PAGE_SIZE
)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER — Reusable card wrapper component
# ═══════════════════════════════════════════════════════════════════════════════
# Card component used for all chart sections with consistent styling

def _card(title, *children, icon="📊"):
    """
    Create a styled card wrapper for dashboard sections.
    
    Each card has a title bar with icon and body content.
    """
    return dbc.Card(
        dbc.CardBody([
            html.H6(
                [html.Span(icon, style={"marginRight": SPACING["sm"]}), title],
                style={
                    "fontWeight": "700",
                    "color": "#1a3c5e",
                    "marginBottom": SPACING["md"],
                    "fontSize": FONT_SIZES["small"]
                },
            ),
            *children,
        ]),
        className="shadow-sm mb-4",
        style={
            "borderRadius": BORDER_RADIUS["lg"],
            "border": "none",
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER — KPI card component
# ═══════════════════════════════════════════════════════════════════════════════
# Small metric card for header KPI display

def _kpi(label, value_id, color="#185FA5"):
    """
    Create a KPI metric card for header summary.
    
    Displays a label and dynamic value with color-coded border.
    """
    return dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.P(
                    label,
                    style={
                        "fontSize": FONT_SIZES["tiny"],
                        "color": "#777",
                        "marginBottom": "2px"
                    }
                ),
                html.H4(
                    id=value_id,
                    children="—",
                    style={
                        "fontWeight": "800",
                        "color": color,
                        "margin": 0,
                        "fontSize": "1.1rem"
                    },
                ),
            ]),
            style={
                "borderRadius": BORDER_RADIUS["md"],
                "border": f"2px solid {color}20",
                "background": f"{color}08"
            },
        ),
        xs=6, sm=4, md=2,
    )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN LAYOUT BUILDER
# ══════════════════════════════════════════════════════════════════════════════
def build_layout():
    """Build the complete dashboard layout with all sections and components."""
    return dbc.Container(
        fluid=True,
        style={
            "fontFamily": "'Segoe UI', sans-serif",
            "backgroundColor": "#f4f6fb",
            "minHeight": "100vh",
            "padding": "0"
        },
        children=[
            # Data stores for client-side state management
            dcc.Store(id="store-country"),
            dcc.Store(id="store-timeseries"),

            # ══════════════════════════════════════════════════════════════════
            # HEADER BANNER — Title and data summary
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                style=HEADER_STYLE,
                children=[
                    dbc.Row([
                        dbc.Col([
                            html.H1(
                                "🦠 COVID-19 Global Pandemic Analysis",
                                style={
                                    "fontWeight": "900",
                                    "fontSize": FONT_SIZES["header_h1"],
                                    "letterSpacing": "-0.5px",
                                    "marginBottom": SPACING["sm"]
                                },
                            ),
                            html.P(
                                "لوحة تحليلية تفاعلية شاملة — بيانات Our World in Data",
                                style={
                                    "opacity": 0.75,
                                    "fontSize": FONT_SIZES["small"],
                                    "margin": 0
                                },
                            ),
                        ], md=8),
                        dbc.Col([
                            html.Div(
                                id="header-data-info",
                                style={
                                    "textAlign": "right",
                                    "opacity": 0.7,
                                    "fontSize": FONT_SIZES["small"],
                                    "paddingTop": SPACING["lg"]
                                }
                            ),
                        ], md=4),
                    ], align="center"),
                ],
            ),

            # ══════════════════════════════════════════════════════════════════
            # MAIN BODY — All dashboard content
            # ══════════════════════════════════════════════════════════════════
            dbc.Container(
                fluid=True,
                style={"padding": f"{SPACING['lg']} {SPACING['xl']}"},
                children=[

                # ── DATA LOADER ────────────────────────────────────────────────
                dbc.Card(
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label(
                                    "📂 مسار ملف البيانات (CSV)",
                                    style={"fontWeight": "600", "fontSize": FONT_SIZES["small"]}
                                ),
                                dbc.Input(
                                    id="input-csv-path",
                                    value="./data/owid_covid_cleaned.csv",
                                    placeholder="مسار محلي أو رابط URL …",
                                    debounce=False,
                                    style={
                                        "fontFamily": "monospace",
                                        "fontSize": FONT_SIZES["small"]
                                    },
                                ),
                            ], md=9),
                            dbc.Col([
                                html.Label(" ", style={"display": "block"}),
                                dbc.Button(
                                    "🔄 تحميل البيانات",
                                    id="btn-load",
                                    color="primary",
                                    className="w-100",
                                    style={"fontWeight": "700"},
                                ),
                            ], md=3),
                        ], align="end"),
                        html.Div(id="load-status", style={"marginTop": "8px", "fontSize": "0.85rem"}),
                    ]),
                    className="mb-4 shadow-sm",
                    style={"borderRadius": "12px", "border": "none", "background": "white"},
                ),

                # ── KPI CARDS ──────────────────────────────────────────────────
                dbc.Row(id="kpi-row", className="mb-4", children=[
                    _kpi("🌍 الدول",              "kpi-countries",  "#185FA5"),
                    _kpi("🦠 إجمالي الإصابات",   "kpi-cases",      "#A32D2D"),
                    _kpi("💀 إجمالي الوفيات",    "kpi-deaths",     "#6B2323"),
                    _kpi("💉 إجمالي التطعيمات",  "kpi-vax",        "#3B6D11"),
                    _kpi("📉 معدل الوفيات CFR",  "kpi-cfr",        "#BA7517"),
                    _kpi("💊 متوسط التطعيم",     "kpi-vax-pct",    "#534AB7"),
                ]),

                # ── CONTROLS PANEL ─────────────────────────────────────────────
                _card("🎛 لوحة التحكم — الفلاتر التفاعلية",
                    *[
                        dbc.Row([
                            # 1️⃣ Continent multi-select
                            dbc.Col([
                                html.Label("1️⃣ اختر القارات", style={"fontWeight": "600"}),
                                dcc.Dropdown(
                                    id="dd-continent",
                                    options=[{"label": c, "value": c} for c in CONTINENT_OPTIONS],
                                    value=CONTINENT_OPTIONS,
                                    multi=True,
                                    placeholder="اختر القارة …",
                                    style={"fontSize": "0.88rem"},
                                ),
                            ], md=4),
                            # 2️⃣ Metric selector
                            dbc.Col([
                                html.Label("2️⃣ المقياس الرئيسي", style={"fontWeight": "600"}),
                                dcc.Dropdown(
                                    id="dd-metric",
                                    options=METRIC_OPTIONS,
                                    value="total_cases",
                                    clearable=False,
                                    style={"fontSize": "0.88rem"},
                                ),
                            ], md=3),
                            # 3️⃣ Top-N slider
                            dbc.Col([
                                html.Label("3️⃣ عدد الدول المعروضة", style={"fontWeight": "600"}),
                                dcc.Slider(
                                    id="slider-topn",
                                    min=5, max=50, step=5, value=15,
                                    marks={i: str(i) for i in range(5, 51, 5)},
                                    tooltip={"placement": "bottom"},
                                ),
                            ], md=3),
                            # 4️⃣ View radio
                            dbc.Col([
                                html.Label("4️⃣ نوع العرض", style={"fontWeight": "600"}),
                                dcc.RadioItems(
                                    id="radio-view",
                                    options=[
                                        {"label": " قيمة مطلقة", "value": "raw"},
                                        {"label": " لكل مليون",  "value": "per_million"},
                                        {"label": " نسبة %",     "value": "pct"},
                                    ],
                                    value="raw",
                                    inputStyle={"marginRight": "4px"},
                                    labelStyle={"display": "block", "fontSize": "0.85rem"},
                                ),
                            ], md=2),
                        ], className="g-3"),
                    ]
                ),

                # ── SECTION DIVIDER helper ─────────────────────────────────────
                # ══════════════════════════════════════════════════════════════
                # SECTION 1 — OVERVIEW  (Week 1)
                # ══════════════════════════════════════════════════════════════
                html.H4("📌 Section 1 — Overview",
                        style={"color": "#1a3c5e", "fontWeight": "800",
                               "borderLeft": "5px solid #185FA5",
                               "paddingLeft": "12px", "margin": "8px 0 16px"}),

                dbc.Row([
                    dbc.Col(_card(
                        "Week 1 — Column Chart (Comparison)",
                        dcc.Graph(id="chart-column", config={"displayModeBar": False}),
                    ), md=6),
                    dbc.Col(_card(
                        "Week 1 — Bar Chart (Comparison)",
                        dcc.Graph(id="chart-bar", config={"displayModeBar": False}),
                    ), md=6),
                ]),

                # ══════════════════════════════════════════════════════════════
                # SECTION 2 — COMPARISONS  (Week 2)
                # ══════════════════════════════════════════════════════════════
                html.H4("📌 Section 2 — Comparisons",
                        style={"color": "#1a3c5e", "fontWeight": "800",
                               "borderLeft": "5px solid #A32D2D",
                               "paddingLeft": "12px", "margin": "8px 0 16px"}),

                dbc.Row([
                    dbc.Col(_card(
                        "Week 2 — Stacked Column Chart",
                        dcc.Graph(id="chart-stacked-col", config={"displayModeBar": False}),
                    ), md=6),
                    dbc.Col(_card(
                        "Week 2 — Stacked Bar Chart",
                        dcc.Graph(id="chart-stacked-bar", config={"displayModeBar": False}),
                    ), md=6),
                ]),
                dbc.Row([
                    dbc.Col(_card(
                        "Week 2 — Clustered Column Chart",
                        dcc.Graph(id="chart-cluster-col", config={"displayModeBar": False}),
                    ), md=6),
                    dbc.Col(_card(
                        "Week 2 — Clustered Bar Chart",
                        dcc.Graph(id="chart-cluster-bar", config={"displayModeBar": False}),
                    ), md=6),
                ]),

                # ══════════════════════════════════════════════════════════════
                # SECTION 3 — RELATIONSHIPS  (Weeks 3–4)
                # ══════════════════════════════════════════════════════════════
                html.H4("📌 Section 3 — Relationships",
                        style={"color": "#1a3c5e", "fontWeight": "800",
                               "borderLeft": "5px solid #3B6D11",
                               "paddingLeft": "12px", "margin": "8px 0 16px"}),

                dbc.Row([
                    dbc.Col(_card(
                        "Week 3 — Scatter Chart (Relationship)",
                        # X / Y axis selectors for scatter
                        dbc.Row([
                            dbc.Col([
                                html.Label("المحور X", style={"fontSize": "0.8rem", "fontWeight": "600"}),
                                dcc.Dropdown(
                                    id="dd-scatter-x",
                                    options=METRIC_OPTIONS,
                                    value="total_cases",
                                    clearable=False,
                                    style={"fontSize": "0.82rem"},
                                ),
                            ], md=6),
                            dbc.Col([
                                html.Label("المحور Y", style={"fontSize": "0.8rem", "fontWeight": "600"}),
                                dcc.Dropdown(
                                    id="dd-scatter-y",
                                    options=METRIC_OPTIONS,
                                    value="total_deaths",
                                    clearable=False,
                                    style={"fontSize": "0.82rem"},
                                ),
                            ], md=6),
                        ], className="mb-2"),
                        dcc.Graph(id="chart-scatter", config={"displayModeBar": False}),
                    ), md=6),
                    dbc.Col(_card(
                        "Week 4 — Bubble Chart (GDP vs Cases)",
                        dcc.Graph(id="chart-bubble", config={"displayModeBar": False}),
                    ), md=6),
                ]),

                # ══════════════════════════════════════════════════════════════
                # SECTION 4 — DISTRIBUTIONS  (Weeks 5–7)
                # ══════════════════════════════════════════════════════════════
                html.H4("📌 Section 4 — Distributions",
                        style={"color": "#1a3c5e", "fontWeight": "800",
                               "borderLeft": "5px solid #BA7517",
                               "paddingLeft": "12px", "margin": "8px 0 16px"}),

                dbc.Row([
                    dbc.Col(_card(
                        "Week 5 — Histogram (Distribution)",
                        dcc.Graph(id="chart-histogram", config={"displayModeBar": False}),
                    ), md=4),
                    dbc.Col(_card(
                        "Week 6 — Box Chart (by Continent)",
                        dcc.Graph(id="chart-box", config={"displayModeBar": False}),
                    ), md=4),
                    dbc.Col(_card(
                        "Week 7 — Violin Chart (by Continent)",
                        dcc.Graph(id="chart-violin", config={"displayModeBar": False}),
                    ), md=4),
                ]),

                # ══════════════════════════════════════════════════════════════
                # SECTION 5 — TRENDS  (Weeks 8–9)
                # ══════════════════════════════════════════════════════════════
                html.H4("📌 Section 5 — Trends (Time-Series)",
                        style={"color": "#1a3c5e", "fontWeight": "800",
                               "borderLeft": "5px solid #534AB7",
                               "paddingLeft": "12px", "margin": "8px 0 16px"}),

                _card(
                    "Week 8 — Line Chart (Time-Series)",
                    dcc.Graph(id="chart-line", config={"displayModeBar": False}),
                ),
                _card(
                    "Week 9 — Area Chart (Time-Series)",
                    dcc.Graph(id="chart-area", config={"displayModeBar": False}),
                ),

                # ══════════════════════════════════════════════════════════════
                # DATA TABLE
                # ══════════════════════════════════════════════════════════════
                html.H4("📌 Data Table",
                        style={"color": "#1a3c5e", "fontWeight": "800",
                               "borderLeft": "5px solid #888",
                               "paddingLeft": "12px", "margin": "8px 0 16px"}),

                _card("📋 جدول البيانات التفصيلي",
                    dbc.Row([
                        dbc.Col(
                            dbc.Input(
                                id="table-search",
                                placeholder="🔍 بحث عن دولة …",
                                debounce=True,
                                style={"fontSize": "0.9rem"},
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Button("⬇️ تصدير CSV", id="btn-export",
                                       color="success", outline=True,
                                       className="w-100"),
                            md=2,
                        ),
                    ], className="mb-3"),
                    dash_table.DataTable(
                        id="data-table",
                        page_size=15,
                        sort_action="native",
                        filter_action="native",
                        style_table={"overflowX": "auto", "borderRadius": "8px"},
                        style_header={
                            "backgroundColor": "#1a3c5e",
                            "color": "white",
                            "fontWeight": "700",
                            "fontSize": "0.82rem",
                            "textAlign": "center",
                        },
                        style_cell={
                            "textAlign": "center",
                            "fontSize": "0.82rem",
                            "padding": "7px 10px",
                            "border": "1px solid #e9ecef",
                        },
                        style_data_conditional=[
                            {"if": {"row_index": "odd"},
                             "backgroundColor": "#f8f9fb"},
                        ],
                    ),
                    dcc.Download(id="download-csv"),
                ),

                # ── footer ─────────────────────────────────────────────────────
                html.Hr(style={"opacity": 0.2}),
                html.P(
                    "🦠 COVID-19 Dashboard  ·  Data: Our World in Data  ·  Built with Plotly Dash",
                    style={"textAlign": "center", "color": "#aaa", "fontSize": "0.8rem", "paddingBottom": "20px"},
                ),
            ]),
        ],
    )
