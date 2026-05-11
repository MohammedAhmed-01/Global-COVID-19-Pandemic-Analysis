"""
dashboard_callbacks.py
=======================
All Dash callbacks for the COVID-19 Global Pandemic Dashboard.

Callbacks implemented
---------------------
  CB-1  load_data          — Load CSV → store-country, store-timeseries, KPIs, status
  CB-2  update_overview    — Week 1  : Column Chart + Bar Chart
  CB-3  update_comparisons — Week 2  : Stacked Column / Stacked Bar /
                                       Clustered Column / Clustered Bar
  CB-4  update_scatter     — Week 3  : Scatter Chart
  CB-5  update_bubble      — Week 4  : Bubble Chart
  CB-6  update_histogram   — Week 5  : Histogram
  CB-7  update_box         — Week 6  : Box Chart
  CB-8  update_violin      — Week 7  : Violin Chart
  CB-9  update_line        — Week 8  : Line Chart (time-series)
  CB-10 update_area        — Week 9  : Area Chart (time-series)
  CB-11 update_table       — Searchable data table
  CB-12 export_csv         — Download filtered CSV
"""

import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dash import callback, Input, Output, State, no_update, dcc
from dash.exceptions import PreventUpdate

# ── Shared constants ──────────────────────────────────────────────────────────
CONTINENT_COLORS = {
    "Asia":          "#185FA5",
    "Europe":        "#A32D2D",
    "Africa":        "#3B6D11",
    "North America": "#BA7517",
    "South America": "#534AB7",
    "Oceania":       "#1D9E75",
}

CHART_LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=10, r=10, t=50, b=30),
    font=dict(family="'Segoe UI', sans-serif", size=11),
    hovermode="closest",
)

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

# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
def fmt(v):
    """Human-readable number formatter."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    v = float(v)
    if v >= 1e9: return f"{v/1e9:.2f}B"
    if v >= 1e6: return f"{v/1e6:.2f}M"
    if v >= 1e3: return f"{v/1e3:.0f}K"
    return f"{v:.1f}"


def _empty_fig(msg="لا تتوفر بيانات كافية"):
    fig = go.Figure()
    fig.add_annotation(text=msg, showarrow=False,
                       font=dict(size=14, color="#aaa"),
                       xref="paper", yref="paper", x=0.5, y=0.5)
    fig.update_layout(**CHART_LAYOUT, height=380)
    return fig


def _load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    return df


def _process_owid(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate full OWID dataset to one row per country (latest date)."""
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if "iso_code" in df.columns:
        df = df[~df["iso_code"].astype(str).str.startswith("OWID")]
    if "date" in df.columns:
        df = df.sort_values("date").groupby("location", as_index=False).last()
    return df


def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise column names & derive missing metrics."""
    rename = {
        "country": "location", "Country": "location",
        "cases": "total_cases", "deaths": "total_deaths",
        "vaccinations": "total_vaccinations",
        "people_fully_vaccinated_per_hundred": "vaccination_rate_pct",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    numeric = [
        "population", "total_cases", "total_deaths", "total_vaccinations",
        "cases_per_million", "deaths_per_million", "vaccination_rate_pct",
        "case_fatality_rate", "gdp_per_capita", "median_age", "population_density",
        "life_expectancy", "human_development_index", "stringency_index",
        "total_cases_per_million", "total_deaths_per_million",
        "new_cases", "new_deaths",
    ]
    for c in numeric:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "cases_per_million" not in df.columns:
        if "total_cases_per_million" in df.columns:
            df["cases_per_million"] = df["total_cases_per_million"]
        elif all(c in df.columns for c in ["total_cases", "population"]):
            df["cases_per_million"] = df["total_cases"] / df["population"] * 1e6

    if "deaths_per_million" not in df.columns:
        if "total_deaths_per_million" in df.columns:
            df["deaths_per_million"] = df["total_deaths_per_million"]
        elif all(c in df.columns for c in ["total_deaths", "population"]):
            df["deaths_per_million"] = df["total_deaths"] / df["population"] * 1e6

    if "case_fatality_rate" not in df.columns:
        if all(c in df.columns for c in ["total_cases", "total_deaths"]):
            df["case_fatality_rate"] = df["total_deaths"] / df["total_cases"] * 100

    if "vaccination_rate_pct" not in df.columns:
        if all(c in df.columns for c in ["total_vaccinations", "population"]):
            df["vaccination_rate_pct"] = df["total_vaccinations"] / df["population"] * 100

    if "continent" not in df.columns:
        df["continent"] = "Unknown"

    return df


def _build_timeseries(path: str) -> pd.DataFrame | None:
    """Build global daily aggregation from full OWID CSV."""
    try:
        cols = ["date", "iso_code", "new_cases", "new_deaths",
                "new_cases_smoothed", "new_deaths_smoothed"]
        raw = pd.read_csv(path, low_memory=False,
                          usecols=lambda c: c in cols)
        if "date" not in raw.columns:
            return None
        raw["date"] = pd.to_datetime(raw["date"], errors="coerce")
        if "iso_code" in raw.columns:
            raw = raw[~raw["iso_code"].astype(str).str.startswith("OWID")]
        agg = raw.groupby("date", as_index=False).sum(numeric_only=True).sort_values("date")
        agg.rename(columns={"new_cases_smoothed": "cases_7day_ma",
                             "new_deaths_smoothed": "deaths_7day_ma"}, inplace=True)
        for c in ["new_cases", "new_deaths", "cases_7day_ma", "deaths_7day_ma"]:
            if c in agg.columns:
                agg[c] = agg[c].replace(0, np.nan)
        return agg
    except Exception:
        return None


def _get_display(df: pd.DataFrame, metric: str, view: str) -> pd.Series:
    base = df[metric].fillna(0) if metric in df.columns else pd.Series(0, index=df.index)
    if view == "per_million" and "population" in df.columns:
        pop = df["population"].replace(0, np.nan)
        return base / pop * 1e6
    if view == "pct" and "population" in df.columns:
        pop = df["population"].replace(0, np.nan)
        return base / pop * 100
    return base


# ══════════════════════════════════════════════════════════════════════════════
# REGISTER ALL CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════
def register_callbacks(app):

    # ──────────────────────────────────────────────────────────────────────────
    # CB-1  LOAD DATA
    # ──────────────────────────────────────────────────────────────────────────
    @app.callback(
        Output("store-country",    "data"),
        Output("store-timeseries", "data"),
        Output("load-status",      "children"),
        Output("kpi-countries",    "children"),
        Output("kpi-cases",        "children"),
        Output("kpi-deaths",       "children"),
        Output("kpi-vax",          "children"),
        Output("kpi-cfr",          "children"),
        Output("kpi-vax-pct",      "children"),
        Output("header-data-info", "children"),
        Input("btn-load",          "n_clicks"),
        State("input-csv-path",    "value"),
        prevent_initial_call=True,
    )
    def load_data(n, path):
        if not path:
            raise PreventUpdate

        try:
            raw = _load_csv(path)
            is_full = ("iso_code" in raw.columns and "date" in raw.columns
                       and len(raw) > 5_000)

            ts_json = None
            if is_full:
                ts = _build_timeseries(path)
                if ts is not None:
                    ts_json = ts.to_json(date_format="iso")
                raw = _process_owid(raw)

            df = _ensure_columns(raw)
            country_json = df.to_json(date_format="iso")

            # KPIs
            n_countries   = len(df)
            total_cases   = df["total_cases"].sum()  if "total_cases"  in df.columns else 0
            total_deaths  = df["total_deaths"].sum() if "total_deaths" in df.columns else 0
            total_vax     = df["total_vaccinations"].sum() if "total_vaccinations" in df.columns else 0
            cfr           = (total_deaths / total_cases * 100) if total_cases > 0 else 0
            avg_vax_pct   = df["vaccination_rate_pct"].mean() if "vaccination_rate_pct" in df.columns else 0

            status = (
                f"✅ تم تحميل {n_countries:,} دولة  ·  "
                f"{'مع بيانات زمنية ✔' if ts_json else 'بدون بيانات زمنية'}"
            )
            info = f"📊 {n_countries:,} دولة | {'بيانات زمنية ✔' if ts_json else '—'}"

            return (
                country_json, ts_json,
                status,
                f"{n_countries:,}",
                fmt(total_cases),
                fmt(total_deaths),
                fmt(total_vax),
                f"{cfr:.2f}%",
                f"{avg_vax_pct:.1f}%" if not np.isnan(avg_vax_pct) else "—",
                info,
            )
        except Exception as e:
            err = f"❌ خطأ: {e}"
            return (no_update,) * 9 + (err, err)

    # ──────────────────────────────────────────────────────────────────────────
    # HELPER — parse store JSON, apply continent/metric/view filters
    # ──────────────────────────────────────────────────────────────────────────
    def _parse_and_filter(store_json, continents, metric, view, top_n):
        if not store_json:
            return None, None
        df = pd.read_json(io.StringIO(store_json))
        df = _ensure_columns(df)
        if continents:
            df = df[df["continent"].isin(continents)]
        df["_display"] = _get_display(df, metric, view)
        df = df.sort_values("_display", ascending=False)
        metric_label = METRIC_LABELS.get(metric, metric)
        top_df = df.dropna(subset=["_display"]).head(top_n)
        return df, top_df, metric_label

    # ──────────────────────────────────────────────────────────────────────────
    # CB-2  WEEK 1 — Column + Bar Charts
    # ──────────────────────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-column", "figure"),
        Output("chart-bar",    "figure"),
        Input("store-country", "data"),
        Input("dd-continent",  "value"),
        Input("dd-metric",     "value"),
        Input("radio-view",    "value"),
        Input("slider-topn",   "value"),
    )
    def update_overview(store_json, continents, metric, view, top_n):
        result = _parse_and_filter(store_json, continents, metric, view, top_n)
        if result is None or result[0] is None:
            return _empty_fig(), _empty_fig()
        _, top_df, mlabel = result

        if top_df.empty:
            return _empty_fig(), _empty_fig()

        colors = [CONTINENT_COLORS.get(c, "#888780") for c in top_df.get("continent", [])]

        # ── Column Chart ───────────────────────────────────────────────────────
        fig_col = go.Figure(go.Bar(
            x=top_df["location"],
            y=top_df["_display"],
            marker_color=colors,
            opacity=0.85,
            text=top_df["_display"].apply(fmt),
            textposition="outside",
            name=mlabel,
        ))
        fig_col.update_layout(
            **CHART_LAYOUT,
            title=f"أعلى {top_n} دولة — Column Chart",
            xaxis=dict(title="الدولة", tickangle=-40, showgrid=False),
            yaxis=dict(title=mlabel, showgrid=True, gridcolor="#eee"),
            height=380, showlegend=False,
        )

        # ── Bar Chart ──────────────────────────────────────────────────────────
        fig_bar = go.Figure(go.Bar(
            x=top_df["_display"],
            y=top_df["location"],
            orientation="h",
            marker_color=colors,
            opacity=0.85,
            text=top_df["_display"].apply(fmt),
            textposition="outside",
            name=mlabel,
        ))
        fig_bar.update_layout(
            **CHART_LAYOUT,
            title=f"أعلى {top_n} دولة — Bar Chart",
            xaxis=dict(title=mlabel, showgrid=True, gridcolor="#eee"),
            yaxis=dict(autorange="reversed", tickfont_size=10),
            height=380, showlegend=False,
        )
        return fig_col, fig_bar

    # ──────────────────────────────────────────────────────────────────────────
    # CB-3  WEEK 2 — Stacked & Clustered Charts
    # ──────────────────────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-stacked-col",  "figure"),
        Output("chart-stacked-bar",  "figure"),
        Output("chart-cluster-col",  "figure"),
        Output("chart-cluster-bar",  "figure"),
        Input("store-country",       "data"),
        Input("dd-continent",        "value"),
        Input("radio-view",          "value"),
    )
    def update_comparisons(store_json, continents, view):
        if not store_json:
            return [_empty_fig()] * 4

        df = pd.read_json(io.StringIO(store_json))
        df = _ensure_columns(df)
        if continents:
            df = df[df["continent"].isin(continents)]

        STACK_METRICS = {}
        for col, lbl in [
            ("total_cases",        "إصابات"),
            ("total_deaths",       "وفيات"),
            ("total_vaccinations", "تطعيمات"),
        ]:
            if col in df.columns:
                STACK_METRICS[lbl] = col

        if len(STACK_METRICS) < 2:
            return [_empty_fig("لا تتوفر أعمدة كافية للمقارنة")] * 4

        agg_df = (
            df[df["continent"] != "Unknown"]
            .groupby("continent")[[*STACK_METRICS.values()]]
            .sum()
            .reset_index()
        )

        mlbls  = list(STACK_METRICS.keys())
        mcols  = list(STACK_METRICS.values())
        colors = ["#185FA5", "#A32D2D", "#3B6D11", "#BA7517"]

        def _add_bars(fig, barmode, horiz=False):
            for i, (lbl, col) in enumerate(zip(mlbls, mcols)):
                kwargs = dict(
                    name=lbl,
                    marker_color=colors[i % len(colors)],
                    opacity=0.85,
                )
                if horiz:
                    fig.add_trace(go.Bar(x=agg_df[col], y=agg_df["continent"],
                                         orientation="h", **kwargs))
                else:
                    fig.add_trace(go.Bar(x=agg_df["continent"], y=agg_df[col], **kwargs))
            fig.update_layout(
                **CHART_LAYOUT,
                barmode=barmode,
                height=370,
                legend=dict(orientation="h", y=-0.18),
                xaxis=dict(showgrid=True, gridcolor="#eee"),
                yaxis=dict(showgrid=True, gridcolor="#eee"),
            )
            return fig

        fig_sc = _add_bars(go.Figure(), "stack")
        fig_sc.update_layout(
            title="Stacked Column — إصابات / وفيات / تطعيمات حسب القارة",
            xaxis_title="القارة", yaxis_title="القيمة",
        )

        fig_sb = _add_bars(go.Figure(), "stack", horiz=True)
        fig_sb.update_layout(
            title="Stacked Bar — إصابات / وفيات / تطعيمات حسب القارة",
            xaxis_title="القيمة", yaxis_title="القارة",
        )

        fig_cc = _add_bars(go.Figure(), "group")
        fig_cc.update_layout(
            title="Clustered Column — مقارنة الإصابات والوفيات والتطعيمات",
            xaxis_title="القارة", yaxis_title="القيمة",
        )

        fig_cb = _add_bars(go.Figure(), "group", horiz=True)
        fig_cb.update_layout(
            title="Clustered Bar — مقارنة الإصابات والوفيات والتطعيمات",
            xaxis_title="القيمة", yaxis_title="القارة",
        )

        return fig_sc, fig_sb, fig_cc, fig_cb

    # ──────────────────────────────────────────────────────────────────────────
    # CB-4  WEEK 3 — Scatter Chart
    # ──────────────────────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-scatter", "figure"),
        Input("store-country",  "data"),
        Input("dd-continent",   "value"),
        Input("dd-scatter-x",   "value"),
        Input("dd-scatter-y",   "value"),
    )
    def update_scatter(store_json, continents, x_col, y_col):
        if not store_json:
            return _empty_fig()

        df = pd.read_json(io.StringIO(store_json))
        df = _ensure_columns(df)
        if continents:
            df = df[df["continent"].isin(continents)]

        if x_col not in df.columns or y_col not in df.columns:
            return _empty_fig(f"العمود '{x_col}' أو '{y_col}' غير موجود")

        sdf = df.dropna(subset=[x_col, y_col, "location", "continent"])

        # Apply log if values span orders of magnitude
        x_label = METRIC_LABELS.get(x_col, x_col)
        y_label = METRIC_LABELS.get(y_col, y_col)

        fig = px.scatter(
            sdf,
            x=x_col, y=y_col,
            color="continent",
            color_discrete_map=CONTINENT_COLORS,
            hover_name="location",
            labels={x_col: x_label, y_col: y_label},
            title=f"{y_label} مقابل {x_label} — Scatter Chart",
            opacity=0.72,
        )
        fig.update_traces(marker=dict(size=8, line=dict(width=0.5, color="white")))
        fig.update_layout(
            **CHART_LAYOUT,
            height=400,
            xaxis=dict(showgrid=True, gridcolor="#eee", title=x_label),
            yaxis=dict(showgrid=True, gridcolor="#eee", title=y_label),
            legend=dict(orientation="h", y=-0.22, font_size=10),
        )
        return fig

    # ──────────────────────────────────────────────────────────────────────────
    # CB-5  WEEK 4 — Bubble Chart
    # ──────────────────────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-bubble", "figure"),
        Input("store-country", "data"),
        Input("dd-continent",  "value"),
    )
    def update_bubble(store_json, continents):
        if not store_json:
            return _empty_fig()

        df = pd.read_json(io.StringIO(store_json))
        df = _ensure_columns(df)
        if continents:
            df = df[df["continent"].isin(continents)]

        needed = ["gdp_per_capita", "total_cases", "population", "continent", "location"]
        bdf = df.dropna(subset=[c for c in needed if c in df.columns])

        if bdf.empty or "gdp_per_capita" not in bdf.columns:
            return _empty_fig("لا تتوفر بيانات GDP")

        bdf = bdf[bdf["population"] > 0].copy()
        bdf["cases_pm"] = bdf["total_cases"] / bdf["population"] * 1e6

        fig = px.scatter(
            bdf,
            x="gdp_per_capita",
            y="cases_pm",
            size="population",
            color="continent",
            color_discrete_map=CONTINENT_COLORS,
            hover_name="location",
            hover_data={"gdp_per_capita": ":,.0f", "cases_pm": ":,.0f", "population": ":,.0f"},
            labels={
                "gdp_per_capita": "GDP للفرد (USD)",
                "cases_pm":       "إصابات / مليون",
                "population":     "عدد السكان",
            },
            title="Bubble Chart — GDP للفرد مقابل الإصابات (حجم الفقاعة = السكان)",
            size_max=55,
            opacity=0.72,
        )
        fig.update_layout(
            **CHART_LAYOUT,
            height=420,
            xaxis=dict(showgrid=True, gridcolor="#eee", title="GDP للفرد (USD)"),
            yaxis=dict(showgrid=True, gridcolor="#eee", title="إصابات / مليون"),
            legend=dict(orientation="h", y=-0.22, font_size=10),
        )
        return fig

    # ──────────────────────────────────────────────────────────────────────────
    # CB-6  WEEK 5 — Histogram
    # ──────────────────────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-histogram", "figure"),
        Input("store-country",    "data"),
        Input("dd-continent",     "value"),
        Input("dd-metric",        "value"),
        Input("radio-view",       "value"),
    )
    def update_histogram(store_json, continents, metric, view):
        if not store_json:
            return _empty_fig()

        df = pd.read_json(io.StringIO(store_json))
        df = _ensure_columns(df)
        if continents:
            df = df[df["continent"].isin(continents)]

        df["_display"] = _get_display(df, metric, view)
        vals = df.dropna(subset=["_display"])["_display"]

        if vals.empty:
            return _empty_fig()

        mlabel = METRIC_LABELS.get(metric, metric)
        fig = px.histogram(
            vals,
            nbins=25,
            title=f"Histogram — توزيع {mlabel}",
            labels={"value": mlabel, "count": "عدد الدول"},
            color_discrete_sequence=["#185FA5"],
            opacity=0.80,
        )
        fig.update_layout(
            **CHART_LAYOUT,
            height=380,
            xaxis=dict(title=mlabel, showgrid=True, gridcolor="#eee"),
            yaxis=dict(title="عدد الدول", showgrid=True, gridcolor="#eee"),
            showlegend=False,
            bargap=0.05,
        )
        return fig

    # ──────────────────────────────────────────────────────────────────────────
    # CB-7  WEEK 6 — Box Chart
    # ──────────────────────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-box",    "figure"),
        Input("store-country", "data"),
        Input("dd-continent",  "value"),
        Input("dd-metric",     "value"),
        Input("radio-view",    "value"),
    )
    def update_box(store_json, continents, metric, view):
        if not store_json:
            return _empty_fig()

        df = pd.read_json(io.StringIO(store_json))
        df = _ensure_columns(df)
        if continents:
            df = df[df["continent"].isin(continents)]

        df["_display"] = _get_display(df, metric, view)
        bdf = df.dropna(subset=["_display", "continent"])
        bdf = bdf[bdf["continent"] != "Unknown"]

        if bdf.empty:
            return _empty_fig()

        mlabel = METRIC_LABELS.get(metric, metric)
        fig = px.box(
            bdf,
            x="continent", y="_display",
            color="continent",
            color_discrete_map=CONTINENT_COLORS,
            points="outliers",
            title=f"Box Chart — توزيع {mlabel} حسب القارة",
            labels={"_display": mlabel, "continent": "القارة"},
        )
        fig.update_layout(
            **CHART_LAYOUT,
            height=390,
            showlegend=False,
            xaxis=dict(title="القارة", showgrid=False),
            yaxis=dict(title=mlabel, showgrid=True, gridcolor="#eee"),
        )
        return fig

    # ──────────────────────────────────────────────────────────────────────────
    # CB-8  WEEK 7 — Violin Chart
    # ──────────────────────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-violin", "figure"),
        Input("store-country", "data"),
        Input("dd-continent",  "value"),
        Input("dd-metric",     "value"),
        Input("radio-view",    "value"),
    )
    def update_violin(store_json, continents, metric, view):
        if not store_json:
            return _empty_fig()

        df = pd.read_json(io.StringIO(store_json))
        df = _ensure_columns(df)
        if continents:
            df = df[df["continent"].isin(continents)]

        df["_display"] = _get_display(df, metric, view)
        vdf = df.dropna(subset=["_display", "continent"])
        vdf = vdf[vdf["continent"] != "Unknown"]

        if vdf.empty:
            return _empty_fig()

        mlabel = METRIC_LABELS.get(metric, metric)
        fig = px.violin(
            vdf,
            x="continent", y="_display",
            color="continent",
            color_discrete_map=CONTINENT_COLORS,
            box=True,
            points="outliers",
            title=f"Violin Chart — توزيع {mlabel} حسب القارة",
            labels={"_display": mlabel, "continent": "القارة"},
        )
        fig.update_layout(
            **CHART_LAYOUT,
            height=400,
            showlegend=False,
            xaxis=dict(title="القارة", showgrid=False),
            yaxis=dict(title=mlabel, showgrid=True, gridcolor="#eee"),
        )
        return fig

    # ──────────────────────────────────────────────────────────────────────────
    # CB-9  WEEK 8 — Line Chart (time-series)
    # ──────────────────────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-line",       "figure"),
        Input("store-timeseries",  "data"),
    )
    def update_line(ts_json):
        if not ts_json:
            return _empty_fig("💡 قم بتحميل ملف OWID الكامل للحصول على التسلسل الزمني")

        ts = pd.read_json(io.StringIO(ts_json))
        if "date" not in ts.columns:
            return _empty_fig()

        ts["date"] = pd.to_datetime(ts["date"], errors="coerce")
        ts = ts.sort_values("date")

        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            subplot_titles=("الحالات الجديدة اليومية", "الوفيات الجديدة اليومية"),
            vertical_spacing=0.12,
        )

        if "new_cases" in ts.columns:
            cdf = ts.dropna(subset=["new_cases"])
            fig.add_trace(go.Scatter(
                x=cdf["date"], y=cdf["new_cases"],
                name="حالات يومية", mode="lines",
                line=dict(color="#B5D4F4", width=1),
                fill="tozeroy", fillcolor="rgba(24,95,165,0.12)",
            ), row=1, col=1)

        if "cases_7day_ma" in ts.columns:
            mdf = ts.dropna(subset=["cases_7day_ma"])
            fig.add_trace(go.Scatter(
                x=mdf["date"], y=mdf["cases_7day_ma"],
                name="MA 7 أيام (إصابات)", mode="lines",
                line=dict(color="#185FA5", width=2.5),
            ), row=1, col=1)

        if "new_deaths" in ts.columns:
            ddf = ts.dropna(subset=["new_deaths"])
            fig.add_trace(go.Scatter(
                x=ddf["date"], y=ddf["new_deaths"],
                name="وفيات يومية", mode="lines",
                line=dict(color="#F09595", width=1),
                fill="tozeroy", fillcolor="rgba(163,45,45,0.10)",
            ), row=2, col=1)

        if "deaths_7day_ma" in ts.columns:
            dmdf = ts.dropna(subset=["deaths_7day_ma"])
            fig.add_trace(go.Scatter(
                x=dmdf["date"], y=dmdf["deaths_7day_ma"],
                name="MA وفيات 7 أيام", mode="lines",
                line=dict(color="#A32D2D", width=2.5),
            ), row=2, col=1)

        fig.update_layout(
            **CHART_LAYOUT,
            title="Line Chart — الحالات والوفيات اليومية عبر الزمن",
            height=500,
            hovermode="x unified",
            legend=dict(orientation="h", y=-0.12, font_size=10),
        )
        fig.update_yaxes(showgrid=True, gridcolor="#eee")
        fig.update_xaxes(showgrid=True, gridcolor="#eee")
        return fig

    # ──────────────────────────────────────────────────────────────────────────
    # CB-10  WEEK 9 — Area Chart (time-series)
    # ──────────────────────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-area",      "figure"),
        Input("store-timeseries", "data"),
    )
    def update_area(ts_json):
        if not ts_json:
            return _empty_fig("💡 قم بتحميل ملف OWID الكامل للحصول على التسلسل الزمني")

        ts = pd.read_json(io.StringIO(ts_json))
        if "date" not in ts.columns:
            return _empty_fig()

        ts["date"] = pd.to_datetime(ts["date"], errors="coerce")
        ts = ts.sort_values("date")

        fig = go.Figure()

        if "new_cases" in ts.columns:
            cdf = ts.dropna(subset=["new_cases"])
            fig.add_trace(go.Scatter(
                x=cdf["date"], y=cdf["new_cases"],
                name="حالات يومية", mode="lines",
                fill="tozeroy",
                line=dict(color="#185FA5", width=1.5),
                fillcolor="rgba(24,95,165,0.22)",
            ))

        if "new_deaths" in ts.columns:
            ddf = ts.dropna(subset=["new_deaths"])
            fig.add_trace(go.Scatter(
                x=ddf["date"], y=ddf["new_deaths"],
                name="وفيات يومية", mode="lines",
                fill="tozeroy",
                line=dict(color="#A32D2D", width=1.5),
                fillcolor="rgba(163,45,45,0.18)",
            ))

        fig.update_layout(
            **CHART_LAYOUT,
            title="Area Chart — الحالات والوفيات اليومية (منطقة مساحية)",
            height=420,
            hovermode="x unified",
            legend=dict(orientation="h", y=-0.14, font_size=10),
            xaxis=dict(title="التاريخ", showgrid=True, gridcolor="#eee"),
            yaxis=dict(title="العدد اليومي", showgrid=True, gridcolor="#eee"),
        )
        return fig

    # ──────────────────────────────────────────────────────────────────────────
    # CB-11  DATA TABLE
    # ──────────────────────────────────────────────────────────────────────────
    @app.callback(
        Output("data-table", "data"),
        Output("data-table", "columns"),
        Input("store-country", "data"),
        Input("dd-continent",  "value"),
        Input("dd-metric",     "value"),
        Input("radio-view",    "value"),
        Input("table-search",  "value"),
    )
    def update_table(store_json, continents, metric, view, search):
        if not store_json:
            return [], []

        df = pd.read_json(io.StringIO(store_json))
        df = _ensure_columns(df)
        if continents:
            df = df[df["continent"].isin(continents)]
        if search:
            df = df[df["location"].str.contains(search, case=False, na=False)]

        want_cols = [c for c in [
            "location", "continent", "total_cases", "total_deaths",
            "cases_per_million", "deaths_per_million", "case_fatality_rate",
            "vaccination_rate_pct", "gdp_per_capita", "population",
        ] if c in df.columns]

        LABEL = {
            "location": "الدولة", "continent": "القارة",
            "total_cases": "الإصابات", "total_deaths": "الوفيات",
            "cases_per_million": "إصابات/مليون", "deaths_per_million": "وفيات/مليون",
            "case_fatality_rate": "CFR %", "vaccination_rate_pct": "تطعيم %",
            "gdp_per_capita": "GDP/فرد", "population": "السكان",
        }

        display_df = df[want_cols].copy().sort_values(
            metric if metric in want_cols else want_cols[2], ascending=False
        ).head(100)

        for c in display_df.columns:
            if display_df[c].dtype in [float, np.float64]:
                if "rate" in c or "pct" in c or "cfr" in c.lower():
                    display_df[c] = display_df[c].apply(
                        lambda x: f"{x:.2f}%" if pd.notna(x) else "—"
                    )
                else:
                    display_df[c] = display_df[c].apply(
                        lambda x: fmt(x) if pd.notna(x) else "—"
                    )

        columns = [{"name": LABEL.get(c, c), "id": c} for c in want_cols]
        return display_df.to_dict("records"), columns

    # ──────────────────────────────────────────────────────────────────────────
    # CB-12  EXPORT CSV
    # ──────────────────────────────────────────────────────────────────────────
    @app.callback(
        Output("download-csv",  "data"),
        Input("btn-export",     "n_clicks"),
        State("store-country",  "data"),
        State("dd-continent",   "value"),
        prevent_initial_call=True,
    )
    def export_csv(n, store_json, continents):
        if not store_json:
            raise PreventUpdate

        df = pd.read_json(io.StringIO(store_json))
        df = _ensure_columns(df)
        if continents:
            df = df[df["continent"].isin(continents)]

        return dcc.send_data_frame(df.to_csv, "covid19_filtered.csv",
                                   index=False, encoding="utf-8-sig")
