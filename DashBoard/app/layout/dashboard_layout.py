"""
dashboard_layout.py  —  Member 5 (Final Version — English, Solo Rows)
"""

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

CONTINENT_OPTIONS = [
    "Asia", "Europe", "Africa", "North America", "South America", "Oceania",
]

METRIC_OPTIONS = [
    {"label": "Total Cases",        "value": "total_cases"},
    {"label": "Total Deaths",       "value": "total_deaths"},
    {"label": "Total Vaccinations", "value": "total_vaccinations"},
    {"label": "Cases per Million",  "value": "cases_per_million"},
    {"label": "Deaths per Million", "value": "deaths_per_million"},
    {"label": "Case Fatality Rate %", "value": "case_fatality_rate"},
    {"label": "Vaccination Rate %", "value": "vaccination_rate_pct"},
    {"label": "GDP per Capita",     "value": "gdp_per_capita"},
]


def _card(title, *children, icon="📊"):
    return dbc.Card(
        dbc.CardBody([
            html.H6(
                [html.Span(icon, style={"marginRight": "6px"}), title],
                style={"fontWeight": "700", "color": "#1a3c5e", "marginBottom": "12px"},
            ),
            *children,
        ]),
        className="shadow-sm mb-4",
        style={"borderRadius": "12px", "border": "none"},
    )


def _kpi(label, value_id, color="#185FA5"):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.P(label, style={"fontSize": "0.75rem", "color": "#777", "marginBottom": "2px"}),
                html.H4(id=value_id, children="—",
                        style={"fontWeight": "800", "color": color, "margin": 0}),
            ]),
            style={"borderRadius": "10px",
                   "border": f"2px solid {color}20",
                   "background": f"{color}08"},
        ),
        xs=6, sm=4, md=2,
    )


def _sec(text, color="#185FA5"):
    return html.H4(text, style={
        "color": "#1a3c5e", "fontWeight": "800",
        "borderLeft": f"5px solid {color}",
        "paddingLeft": "12px", "margin": "8px 0 16px",
    })


def _g(gid):
    return dcc.Graph(id=gid, config={"displayModeBar": False})


def build_layout():
    return dbc.Container(fluid=True,
        style={"fontFamily": "'Segoe UI',sans-serif",
               "backgroundColor": "#f4f6fb", "minHeight": "100vh", "padding": "0"},
        children=[

            dcc.Store(id="store-country"),
            dcc.Store(id="store-timeseries"),
            dcc.Store(id="store-cont-ts"),

            # HEADER
            html.Div(style={
                "background": "linear-gradient(135deg,#0d2137 0%,#1a3c5e 60%,#185FA5 100%)",
                "padding": "28px 40px 22px", "color": "white",
                "boxShadow": "0 4px 20px rgba(0,0,0,0.25)",
            }, children=[
                dbc.Row([
                    dbc.Col([
                        html.H1("🦠 COVID-19 Global Pandemic Analysis",
                                style={"fontWeight": "900", "fontSize": "1.9rem",
                                       "letterSpacing": "-0.5px", "marginBottom": "4px"}),
                        html.P("Interactive Analytical Dashboard — Our World in Data",
                               style={"opacity": 0.75, "fontSize": "0.9rem", "margin": 0}),
                    ], md=8),
                    dbc.Col([
                        html.Div(id="header-data-info",
                                 style={"textAlign": "right", "opacity": 0.7,
                                        "fontSize": "0.82rem", "paddingTop": "10px"}),
                    ], md=4),
                ], align="center"),
            ]),

            dbc.Container(fluid=True, style={"padding": "24px 32px"}, children=[

                # DATA LOADER
                dbc.Card(dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("📂 Data File Path (CSV)", style={"fontWeight": "600"}),
                            dbc.Input(id="input-csv-path",
                                      value=r"F:\faculty\Level 3 S_2\Data Visualization\Global COVID-19 Pandemic Analysis\Global-COVID-19-Pandemic-Analysis\Data\Processed\final_dataset.csv",
                                      placeholder="Local path …",
                                      debounce=False,
                                      style={"fontFamily": "monospace", "fontSize": "0.85rem"}),
                        ], md=9),
                        dbc.Col([
                            html.Label(" ", style={"display": "block"}),
                            dbc.Button("🔄 Load Data", id="btn-load",
                                       color="primary", className="w-100",
                                       style={"fontWeight": "700"}),
                        ], md=3),
                    ], align="end"),
                    html.Div(id="load-status", style={"marginTop": "8px", "fontSize": "0.85rem"}),
                ]), className="mb-4 shadow-sm",
                   style={"borderRadius": "12px", "border": "none", "background": "white"}),

                # KPIs
                dbc.Row(className="mb-4", children=[
                    _kpi("🌍 Countries",          "kpi-countries", "#185FA5"),
                    _kpi("🦠 Total Cases",        "kpi-cases",     "#A32D2D"),
                    _kpi("💀 Total Deaths",       "kpi-deaths",    "#6B2323"),
                    _kpi("💉 Total Vaccinations", "kpi-vax",       "#3B6D11"),
                    _kpi("📉 Case Fatality Rate", "kpi-cfr",       "#BA7517"),
                    _kpi("💊 Avg Vaccination",    "kpi-vax-pct",   "#534AB7"),
                ]),

                # CONTROLS
                _card("🎛 Dashboard Controls — Interactive Filters",
                    dbc.Row([
                        dbc.Col([
                            html.Label("1️⃣ Select Continents", style={"fontWeight": "600"}),
                            dcc.Dropdown(
                                id="dd-continent",
                                options=[{"label": c, "value": c} for c in CONTINENT_OPTIONS],
                                value=CONTINENT_OPTIONS, multi=True,
                                placeholder="Select continent …",
                                style={"fontSize": "0.88rem"},
                            ),
                        ], md=4),
                        dbc.Col([
                            html.Label("2️⃣ Primary Metric", style={"fontWeight": "600"}),
                            dcc.Dropdown(id="dd-metric", options=METRIC_OPTIONS,
                                         value="total_cases", clearable=False,
                                         style={"fontSize": "0.88rem"}),
                        ], md=3),
                        dbc.Col([
                            html.Label("3️⃣ Top-N Countries", style={"fontWeight": "600"}),
                            dcc.Slider(id="slider-topn", min=5, max=30, step=5, value=10,
                                       marks={i: str(i) for i in range(5, 31, 5)},
                                       tooltip={"placement": "bottom"}),
                        ], md=3),
                        dbc.Col([
                            html.Label("4️⃣ View Type", style={"fontWeight": "600"}),
                            dcc.RadioItems(id="radio-view",
                                options=[
                                    {"label": " Absolute Value", "value": "raw"},
                                    {"label": " Per Million",    "value": "per_million"},
                                    {"label": " Percentage %",  "value": "pct"},
                                ],
                                value="raw",
                                inputStyle={"marginRight": "4px"},
                                labelStyle={"display": "block", "fontSize": "0.85rem"}),
                        ], md=2),
                    ], className="g-3"),
                ),

                # ── SECTION 1: OVERVIEW ───────────────────────────────────────

                dbc.Row([dbc.Col(
                    _card("Column Chart — Top Countries", _g("chart-column")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("Bar Chart — Top Countries", _g("chart-bar")),
                    md=12)]),

                # ── SECTION 2: COMPARISONS ────────────────────────────────────

                dbc.Row([dbc.Col(
                    _card("Stacked Column — Cases / Vaccinations", _g("chart-stacked-col")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("Stacked Bar — Cases / Vaccinations", _g("chart-stacked-bar")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("Clustered Column — Comparison by Continent", _g("chart-cluster-col")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("Clustered Bar — Comparison by Continent", _g("chart-cluster-bar")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("Chart 3-1 — Top N Countries by Total COVID-19 Cases",
                          _g("chart-m3-top10")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("Chart 3-2 — Total Deaths by Continent",
                          _g("chart-m3-deaths-cont")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("Chart 3-3 — Cases vs Vaccinations (100% Stacked)",
                          _g("chart-m3-stacked-pct")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("Chart 3-4 — Absolute Values Log Scale (Grouped)",
                          _g("chart-m3-grouped-log")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("Chart 3-5 — Average Cases per Million by Continent",
                          _g("chart-m3-cpm")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("Chart 3-6 — Average Deaths per Million by Continent",
                          _g("chart-m3-dpm")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("Chart 3-7 — Average Vaccination Rate (%) by Continent",
                          _g("chart-m3-vaxpct")),
                    md=12)]),

                # ── SECTION 3: RELATIONSHIPS ──────────────────────────────────

                dbc.Row([dbc.Col(
                    _card("S1 — GDP per Capita vs COVID-19 Cases per Million",
                          _g("chart-m4-gdp-cases")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("S2 — Population Size vs Total COVID-19 Deaths",
                          _g("chart-m4-pop-deaths")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("B1 — Bubble: GDP per Capita vs Vaccination Rate  (bubble size = population)",
                          _g("chart-m4-bubble")),
                    md=12)]),

                # ── SECTION 4: DISTRIBUTIONS ──────────────────────────────────

                dbc.Row([dbc.Col(
                    _card("Chart 4-1 — Histogram: Cases Distribution (Log X)",
                          _g("chart-m3-hist")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("Chart 4-2 — Box Plot: Case Fatality Rate by Continent",
                          _g("chart-m3-box")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("Chart 4-3 — Violin: Vaccination Rate Distribution by Continent",
                          _g("chart-m3-violin")),
                    md=12)]),

                # ── SECTION 5: TRENDS ─────────────────────────────────────────

                dbc.Row([dbc.Col(
                    _card("T1 — Global New Cases Over Time",
                          _g("chart-m4-global-cases")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("T2 — Global Vaccination Trends Over Time (Area Chart)",
                          _g("chart-m4-global-vax")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("T3 — New Cases by Continent Over Time",
                          _g("chart-m4-cont-cases")),
                    md=12)]),

                dbc.Row([dbc.Col(
                    _card("T4 — Vaccination Trends by Continent Over Time",
                          _g("chart-m4-cont-vax")),
                    md=12)]),

                # ── DATA TABLE ────────────────────────────────────────────────
                _card("Detailed Data Table",
                    dbc.Row([
                        dbc.Col(dbc.Input(id="table-search",
                                          placeholder="🔍 Search for country …",
                                          debounce=True,
                                          style={"fontSize": "0.9rem"}), md=4),
                        dbc.Col(dbc.Button("⬇️ Export CSV", id="btn-export",
                                           color="success", outline=True,
                                           className="w-100"), md=2),
                    ], className="mb-3"),
                    dash_table.DataTable(
                        id="data-table", page_size=15,
                        sort_action="native", filter_action="native",
                        style_table={"overflowX": "auto", "borderRadius": "8px"},
                        style_header={"backgroundColor": "#1a3c5e", "color": "white",
                                      "fontWeight": "700", "fontSize": "0.82rem",
                                      "textAlign": "center"},
                        style_cell={"textAlign": "center", "fontSize": "0.82rem",
                                    "padding": "7px 10px", "border": "1px solid #e9ecef"},
                        style_data_conditional=[
                            {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fb"},
                        ],
                    ),
                    dcc.Download(id="download-csv"),
                ),

                html.Hr(style={"opacity": 0.2}),
                html.P(
                    "🦠 COVID-19 Dashboard  ·  Data: Our World in Data  ·  Built with Plotly Dash",
                    style={"textAlign": "center", "color": "#aaa",
                           "fontSize": "0.8rem", "paddingBottom": "20px"},
                ),
            ]),
        ],
    )
