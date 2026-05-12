"""
dashboard_callbacks.py  —  Member 5 (Final — all M3 & M4 charts integrated)
"""

from __future__ import annotations

import io
import warnings
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import Input, Output, State, no_update, dcc
from dash.exceptions import PreventUpdate

warnings.filterwarnings("ignore")

# ── Palettes ──────────────────────────────────────────────────────────────────
CONTINENT_COLORS = {
    "Asia":          "#185FA5",
    "Europe":        "#A32D2D",
    "Africa":        "#3B6D11",
    "North America": "#BA7517",
    "South America": "#534AB7",
    "Oceania":       "#1D9E75",
}

COLOR_CASES        = '#4E79A7'
COLOR_CASES_LIGHT  = '#A8CFEB'
COLOR_DEATHS       = '#E15759'
COLOR_VACCINATIONS = '#59A14F'
COLOR_TEXT         = '#000000'
COLOR_GRID         = '#E0E0E0'
COLOR_BORDER       = '#000000'
COLOR_BACKGROUND   = '#FFFFFF'
COLOR_GRAY_LIGHT   = '#D3D3D3'

M4_CONTINENT_COLORS = {
    "Asia":          "lightblue",
    "Europe":        "lightcoral",
    "Africa":        "lightgreen",
    "Oceania":       "plum",
    "North America": "lightsalmon",
    "South America": "lightseagreen",
}

CHART_LAYOUT = dict(
    plot_bgcolor="white", paper_bgcolor="white",
    margin=dict(l=10, r=10, t=50, b=30),
    font=dict(family="'Segoe UI', sans-serif", size=11),
    hovermode="closest",
)

METRIC_LABELS = {
    "total_cases":          "Total Cases",
    "total_deaths":         "Total Deaths",
    "total_vaccinations":   "Total Vaccinations",
    "cases_per_million":    "Cases per Million",
    "deaths_per_million":   "Deaths per Million",
    "case_fatality_rate":   "Case Fatality Rate %",
    "vaccination_rate_pct": "Vaccination Rate %",
    "gdp_per_capita":       "GDP per Capita",
}


# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
def fmt(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    v = float(v)
    if v >= 1e9: return f"{v/1e9:.2f}B"
    if v >= 1e6: return f"{v/1e6:.2f}M"
    if v >= 1e3: return f"{v/1e3:.0f}K"
    return f"{v:.1f}"


def _fmt(val, precision=1):
    if pd.isna(val): return "N/A"
    if abs(val) >= 1e9: return f"{val/1e9:.{precision}f}B"
    if abs(val) >= 1e6: return f"{val/1e6:.{precision}f}M"
    if abs(val) >= 1e3: return f"{val/1e3:.{precision}f}K"
    return f"{val:.{precision}f}"


def _fmt_percent(val, precision=1):
    if pd.isna(val): return "N/A"
    return f"{val:.{precision}f}%"


def _empty_fig(msg="No sufficient data available"):
    fig = go.Figure()
    fig.add_annotation(text=msg, showarrow=False,
                       font=dict(size=14, color="#aaa"),
                       xref="paper", yref="paper", x=0.5, y=0.5)
    fig.update_layout(**CHART_LAYOUT, height=380)
    return fig


def _m3_base_layout(title, xaxis_title, yaxis_title,
                    y_zero=True, height=600, use_log=False,
                    legend_y=1.12, show_legend=True):
    axis_common = dict(
        showgrid=True, gridcolor=COLOR_GRID, gridwidth=1,
        linecolor=COLOR_BORDER, linewidth=2, mirror=True, showline=True,
    )
    return dict(
        template="plotly_white",
        title=dict(text=f"<b>{title}</b>",
                   font=dict(color=COLOR_TEXT, size=16, family="Arial"),
                   x=0.5, xanchor="center", y=0.98, yanchor="top"),
        xaxis=dict(
            title=dict(text=f"<b>{xaxis_title}</b>",
                       font=dict(color=COLOR_TEXT, size=14, family="Arial")),
            tickfont=dict(color=COLOR_TEXT, size=12, family="Arial"),
            tickangle=0, **axis_common,
        ),
        yaxis=dict(
            title=dict(text=f"<b>{yaxis_title}</b>",
                       font=dict(color=COLOR_TEXT, size=14, family="Arial"),
                       standoff=15),
            tickfont=dict(color=COLOR_TEXT, size=12, family="Arial"),
            type="log" if use_log else "linear",
            rangemode="tozero" if (y_zero and not use_log) else "normal",
            **axis_common,
        ),
        plot_bgcolor=COLOR_BACKGROUND, paper_bgcolor=COLOR_BACKGROUND,
        font=dict(color=COLOR_TEXT, family="Arial", size=12),
        legend=dict(
            font=dict(color=COLOR_TEXT, size=12, family="Arial"),
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor=COLOR_BORDER, borderwidth=1,
            xanchor="center", x=0.5, yanchor="bottom", y=legend_y,
            orientation="h", itemsizing="constant",
        ),
        showlegend=show_legend,
        margin=dict(l=100, r=60, t=130, b=100),
        height=height,
    )


def _load_csv(path):
    return pd.read_csv(path, low_memory=False)


def _ensure_continents_list(continents):
    """Ensure continents is a list or None."""
    if continents is None or (isinstance(continents, list) and len(continents) == 0):
        return None
    if isinstance(continents, str):
        return [continents]
    if isinstance(continents, (list, tuple)):
        return list(continents)
    return None


def _process_owid(df):
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if "iso_code" in df.columns:
        df = df[~df["iso_code"].astype(str).str.startswith("OWID")]
    if "date" in df.columns:
        df = df.sort_values("date").groupby("location", as_index=False).last()
    return df


def _ensure_columns(df):
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
        "avg_cases_per_million", "avg_deaths_per_million", "avg_vaccination_rate",
    ]
    for c in numeric:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "cases_per_million" not in df.columns:
        if "total_cases_per_million" in df.columns:
            df["cases_per_million"] = df["total_cases_per_million"]
        elif all(c in df.columns for c in ["total_cases", "population"]):
            pop = pd.to_numeric(df["population"], errors="coerce").replace(0, np.nan)
            df["cases_per_million"] = df["total_cases"] / pop * 1e6

    if "deaths_per_million" not in df.columns:
        if "total_deaths_per_million" in df.columns:
            df["deaths_per_million"] = df["total_deaths_per_million"]
        elif all(c in df.columns for c in ["total_deaths", "population"]):
            pop = pd.to_numeric(df["population"], errors="coerce").replace(0, np.nan)
            df["deaths_per_million"] = df["total_deaths"] / pop * 1e6

    if "case_fatality_rate" not in df.columns:
        if all(c in df.columns for c in ["total_cases", "total_deaths"]):
            cases = pd.to_numeric(df["total_cases"], errors="coerce").replace(0, np.nan)
            df["case_fatality_rate"] = df["total_deaths"] / cases * 100

    if "vaccination_rate_pct" not in df.columns:
        if all(c in df.columns for c in ["total_vaccinations", "population"]):
            pop = pd.to_numeric(df["population"], errors="coerce").replace(0, np.nan)
            df["vaccination_rate_pct"] = df["total_vaccinations"] / pop * 100

    if "continent" not in df.columns:
        df["continent"] = "Unknown"

    return df


def _build_timeseries(path):
    try:
        raw = pd.read_csv(path, low_memory=False)
        if "date" not in raw.columns:
            return None, None
        raw["date"] = pd.to_datetime(raw["date"], errors="coerce")
        if "iso_code" in raw.columns:
            raw = raw[~raw["iso_code"].astype(str).str.startswith("OWID")]

        agg_cols = [c for c in ["new_cases", "new_deaths", "new_vaccinations",
                                 "new_cases_smoothed", "new_deaths_smoothed"]
                    if c in raw.columns]
        global_ts = raw.groupby("date", as_index=False)[agg_cols].sum(numeric_only=True).sort_values("date")
        global_ts.rename(columns={"new_cases_smoothed": "cases_7day_ma",
                                   "new_deaths_smoothed": "deaths_7day_ma"}, inplace=True)
        if "new_vaccinations" in global_ts.columns:
            global_ts["new_vaccinations_7day_ma"] = (
                global_ts["new_vaccinations"].rolling(window=7, min_periods=1).mean()
            )
        for c in ["new_cases", "new_deaths", "cases_7day_ma", "deaths_7day_ma"]:
            if c in global_ts.columns:
                global_ts[c] = global_ts[c].replace(0, np.nan)

        cont_ts = None
        if "continent" in raw.columns:
            cont_agg_cols = [c for c in ["new_cases", "new_vaccinations"] if c in raw.columns]
            cont_ts = (raw.dropna(subset=["continent"])
                          .groupby(["continent", "date"], as_index=False)[cont_agg_cols]
                          .sum(numeric_only=True)
                          .sort_values(["continent", "date"]))
            if "new_cases" in cont_ts.columns:
                cont_ts["new_cases_7day_ma"] = (
                    cont_ts.groupby("continent")["new_cases"]
                           .transform(lambda x: x.rolling(7, min_periods=1).mean())
                )
            if "new_vaccinations" in cont_ts.columns:
                cont_ts["new_vaccinations_7day_ma"] = (
                    cont_ts.groupby("continent")["new_vaccinations"]
                           .transform(lambda x: x.rolling(7, min_periods=1).mean())
                )
        return global_ts, cont_ts
    except Exception as e:
        print(f"_build_timeseries error: {e}")
        return None, None


def _get_display(df, metric, view):
    if not metric or metric not in df.columns:
        return pd.Series(0, index=df.index)
    
    try:
        base = df[metric].fillna(0)
        base = pd.to_numeric(base, errors="coerce").fillna(0)
    except Exception:
        return pd.Series(0, index=df.index)
    
    try:
        if view == "per_million" and "population" in df.columns:
            pop = pd.to_numeric(df["population"], errors="coerce")
            pop = pop.replace(0, np.nan)
            return base / pop * 1e6
        if view == "pct" and "population" in df.columns:
            pop = pd.to_numeric(df["population"], errors="coerce")
            pop = pop.replace(0, np.nan)
            return base / pop * 100
    except Exception:
        pass
    
    return base


def _parse_store(store_json, continents, metric, view, top_n):
    if not store_json:
        return None, None, None
    
    try:
        df = pd.read_json(io.StringIO(store_json))
        df = _ensure_columns(df)
        
        # Ensure continent column is string type
        if "continent" in df.columns:
            df["continent"] = df["continent"].astype(str).str.strip()
        
        continents = _ensure_continents_list(continents)
        if continents and "continent" in df.columns:
            # Convert continents list to list of strings
            continents = [str(c).strip() for c in continents]
            df = df[df["continent"].isin(continents)]
        
        df["_display"] = _get_display(df, metric, view)
        df["_display"] = pd.to_numeric(df["_display"], errors="coerce")
        
        df = df.sort_values("_display", ascending=False)
        top_n = int(top_n) if top_n else 10
        top_df = df.dropna(subset=["_display"]).head(top_n)
        mlabel = METRIC_LABELS.get(metric, metric)
        return df, top_df, mlabel
    except Exception as e:
        print(f"Error in _parse_store: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


# ══════════════════════════════════════════════════════════════════════════════
# MEMBER 5 — OVERVIEW (Week 1)
# ══════════════════════════════════════════════════════════════════════════════
def update_overview(store_json, continents, metric, view, top_n):
    df, top_df, mlabel = _parse_store(store_json, continents, metric, view, top_n)
    if top_df is None or top_df.empty:
        return _empty_fig(), _empty_fig()

    # First country (highest value) gets distinct color, rest all same color
    n = len(top_df)
    FIRST_COL_COLOR = COLOR_DEATHS   # red for top country
    OTHER_COL_COLOR = COLOR_CASES    # blue for the rest
    # Column chart: descending, first = biggest = red
    col_colors = [FIRST_COL_COLOR] + [OTHER_COL_COLOR] * (n - 1)

    # Bar chart: sort ascending so biggest country is LAST in list = appears at TOP naturally
    top_df_bar = top_df.sort_values("_display", ascending=True)
    bar_colors = [OTHER_COL_COLOR] * (n - 1) + [FIRST_COL_COLOR]  # last = biggest = red

    BORDER_SHAPE = dict(type="rect", xref="paper", yref="paper",
                        x0=0, y0=0, x1=1, y1=1,
                        line=dict(color=COLOR_BORDER, width=2),
                        fillcolor="rgba(0,0,0,0)")

    fig_col = go.Figure(go.Bar(
        x=top_df["location"], y=top_df["_display"],
        marker=dict(color=col_colors, opacity=0.85, line=dict(color=COLOR_BORDER, width=1.2)),
        text=top_df["_display"].apply(fmt), textposition="outside",
    ))
    fig_col.update_layout(**CHART_LAYOUT,
                          title=f"Top {top_n} Countries — {mlabel} — Column Chart",
                          xaxis=dict(title="Country", tickangle=-40, showgrid=False,
                                     linecolor=COLOR_BORDER, linewidth=2, mirror=True, showline=True),
                          yaxis=dict(title=mlabel, showgrid=True, gridcolor="#eee",
                                     linecolor=COLOR_BORDER, linewidth=2, mirror=True, showline=True),
                          height=380, showlegend=False,
                          shapes=[BORDER_SHAPE])

    fig_bar = go.Figure(go.Bar(
        x=top_df_bar["_display"], y=top_df_bar["location"],
        orientation="h",
        marker=dict(color=bar_colors, opacity=0.85, line=dict(color=COLOR_BORDER, width=1.2)),
        text=top_df_bar["_display"].apply(fmt), textposition="outside",
    ))
    fig_bar.update_layout(**CHART_LAYOUT,
                          title=f"Top {top_n} Countries — Bar Chart",
                          xaxis=dict(title=mlabel, showgrid=True, gridcolor="#eee",
                                     linecolor=COLOR_BORDER, linewidth=2, mirror=True, showline=True),
                          yaxis=dict(tickfont_size=10,
                                     linecolor=COLOR_BORDER, linewidth=2, mirror=True, showline=True),
                          height=380, showlegend=False,
                          shapes=[BORDER_SHAPE])
    return fig_col, fig_bar


# ══════════════════════════════════════════════════════════════════════════════
# MEMBER 3 — CHART 3-1: Top N Countries by Total Cases
# ══════════════════════════════════════════════════════════════════════════════
def m3_top10_cases(df, top_n=10):
    try:
        top_n = int(top_n) if top_n else 10
    except (ValueError, TypeError):
        top_n = 10
    
    name_col = None
    for c in ("location", "country", "Country", "Location", "name", "Name"):
        if c in df.columns:
            name_col = c
            break
    if name_col is None:
        return _empty_fig("No country name column found")

    df_work = df[[name_col, "total_cases"]].copy()
    df_work[name_col] = df_work[name_col].astype(str).str.strip()
    df_work["total_cases"] = pd.to_numeric(df_work["total_cases"], errors="coerce")

    data = (df_work.dropna(subset=["total_cases"])
                   .query("total_cases > 0")
                   .nlargest(top_n, "total_cases")
                   .sort_values("total_cases", ascending=True)
                   .reset_index(drop=True))

    if len(data) < 2:
        return _empty_fig("Insufficient data")

    country_order = data[name_col].tolist()
    top_country = data.iloc[-1][name_col]
    bar_colors = [COLOR_DEATHS if c == top_country else COLOR_CASES for c in data[name_col]]

    fig = go.Figure(go.Bar(
        x=data["total_cases"], y=data[name_col], orientation="h",
        marker=dict(color=bar_colors, line=dict(color=COLOR_BORDER, width=1.2)),
        text=[_fmt(v) for v in data["total_cases"]],
        textposition="outside", textfont=dict(color=COLOR_TEXT, size=12),
        hovertemplate="<b>%{y}</b><br>Total Cases: %{x:,.0f}<extra></extra>",
        showlegend=False,
    ))
    layout = _m3_base_layout(
        f"Top {top_n} Countries by Total COVID-19 Cases",
        "Total Cases", "Country",
        y_zero=False, height=max(400, top_n * 55), show_legend=False,
    )
    layout["xaxis"]["range"] = [0, data["total_cases"].max() * 1.28]
    layout["yaxis"].update(
        type="category", categoryorder="array", categoryarray=country_order,
        tickfont=dict(color=COLOR_TEXT, size=12, family="Arial"),
    )
    fig.update_layout(**layout)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MEMBER 3 — CHART 3-2: Total Deaths by Continent
# ══════════════════════════════════════════════════════════════════════════════
def m3_deaths_by_continent(df):
    if "continent" not in df.columns:
        return _empty_fig()
    df_work = df[["continent", "total_deaths"]].copy()
    df_work["total_deaths"] = pd.to_numeric(df_work["total_deaths"], errors="coerce")

    if df["continent"].nunique() <= 8 and len(df) <= 10:
        data = df_work.dropna().sort_values("total_deaths", ascending=False).reset_index(drop=True)
    else:
        data = (df_work.dropna()
                       .groupby("continent", as_index=False)["total_deaths"].sum()
                       .sort_values("total_deaths", ascending=False)
                       .reset_index(drop=True))

    if data.empty:
        return _empty_fig()

    # First bar (biggest continent) gets distinct color, rest same
    n = len(data)
    bar_colors = [COLOR_DEATHS] + ["#4E79A7"] * (n - 1)

    fig = go.Figure(go.Bar(
        x=data["continent"], y=data["total_deaths"],
        marker=dict(color=bar_colors, line=dict(color=COLOR_BORDER, width=1.2)),
        text=[_fmt(v) for v in data["total_deaths"]],
        textposition="outside", textfont=dict(color=COLOR_TEXT, size=12),
        hovertemplate="<b>%{x}</b><br>Total Deaths: %{y:,.0f}<extra></extra>",
        showlegend=False,
    ))
    layout = _m3_base_layout("Total COVID-19 Deaths by Continent",
                             "Continent", "Total Deaths", height=600, show_legend=False)
    layout["yaxis"]["range"] = [0, data["total_deaths"].max() * 1.2]
    fig.update_layout(**layout)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MEMBER 3 — CHART 3-3: 100% Stacked
# ══════════════════════════════════════════════════════════════════════════════
def m3_stacked_pct(df):
    if "continent" not in df.columns:
        return _empty_fig()
    if len(df) > 10:
        agg = (df[df["continent"] != "Unknown"]
               .groupby("continent", as_index=False)
               [["total_cases", "total_vaccinations"]].sum())
    else:
        agg = df[["continent", "total_cases", "total_vaccinations"]].copy()
    for col in ["total_cases", "total_vaccinations"]:
        agg[col] = pd.to_numeric(agg[col], errors="coerce")
    data = agg.dropna().copy()
    if data.empty:
        return _empty_fig()
    total = data["total_cases"] + data["total_vaccinations"]
    data["pct_cases"]        = data["total_cases"]        / total * 100
    data["pct_vaccinations"] = data["total_vaccinations"] / total * 100
    data = data.sort_values("pct_vaccinations", ascending=False).reset_index(drop=True)

    fig = go.Figure()
    for col, name, color in [("pct_cases", "Cases", COLOR_CASES),
                              ("pct_vaccinations", "Vaccinations", COLOR_VACCINATIONS)]:
        fig.add_trace(go.Bar(
            x=data["continent"], y=data[col], name=name,
            marker=dict(color=color, line=dict(color=COLOR_BORDER, width=0.8)),
            text=[_fmt_percent(v) if v >= 3 else "" for v in data[col]],
            textposition="inside", textfont=dict(color="white", size=11),
            hovertemplate=f"<b>%{{x}}</b><br>{name}: %{{y:.1f}}%<extra></extra>",
        ))
    layout = _m3_base_layout(
        "COVID-19 Metrics by Continent — Cases vs Vaccinations (100% Stacked)",
        "Continent", "Contribution (%)", height=620,
    )
    layout["barmode"] = "stack"
    layout["yaxis"]["range"] = [0, 100]
    fig.update_layout(**layout)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MEMBER 3 — CHART 3-4: Grouped Log
# ══════════════════════════════════════════════════════════════════════════════
def m3_grouped_log(df):
    if "continent" not in df.columns:
        return _empty_fig()
    if len(df) > 10:
        agg = (df[df["continent"] != "Unknown"]
               .groupby("continent", as_index=False)
               [["total_cases", "total_deaths", "total_vaccinations"]].sum())
    else:
        agg = df[["continent", "total_cases", "total_deaths", "total_vaccinations"]].copy()
    for col in ["total_cases", "total_deaths", "total_vaccinations"]:
        agg[col] = pd.to_numeric(agg[col], errors="coerce")
    data = agg.dropna().sort_values("total_vaccinations", ascending=False).reset_index(drop=True)
    if data.empty:
        return _empty_fig()
    fig = go.Figure()
    for col, name, color in [("total_cases", "Cases", COLOR_CASES),
                              ("total_deaths", "Deaths", COLOR_DEATHS),
                              ("total_vaccinations", "Vaccinations", COLOR_VACCINATIONS)]:
        fig.add_trace(go.Bar(
            x=data["continent"], y=data[col], name=name,
            marker=dict(color=color, line=dict(color=COLOR_BORDER, width=0.8)),
            text=[_fmt(v) for v in data[col]],
            textposition="outside", textfont=dict(color=COLOR_TEXT, size=10),
            hovertemplate=f"<b>%{{x}}</b><br>{name}: %{{y:,.0f}}<extra></extra>",
        ))
    layout = _m3_base_layout(
        "COVID-19 Metrics by Continent — Absolute Values (Log Scale)",
        "Continent", "Count (Log Scale)", y_zero=False, use_log=True, height=620,
    )
    layout["barmode"] = "group"
    fig.update_layout(**layout)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MEMBER 3 — CHARTS 3-5 / 3-6 / 3-7
# ══════════════════════════════════════════════════════════════════════════════
def _m3_continent_bar(df, col, single_color, title, y_label, y_range=None, is_pct=False):
    if "continent" not in df.columns:
        return _empty_fig()
    if col not in df.columns:
        mapping = {
            "avg_cases_per_million":  "cases_per_million",
            "avg_deaths_per_million": "deaths_per_million",
            "avg_vaccination_rate":   "vaccination_rate_pct",
        }
        src = mapping.get(col)
        if src and src in df.columns:
            tmp = df.dropna(subset=[src, "continent"])
            if is_pct:
                tmp = tmp.query(f"0 <= {src} <= 100")
            df = tmp.groupby("continent", as_index=False)[src].mean().rename(columns={src: col})
        else:
            return _empty_fig(f"Column not found")

    df_work = df[["continent", col]].copy()
    df_work[col] = pd.to_numeric(df_work[col], errors="coerce")
    if is_pct:
        data = df_work.dropna().query(f"0 <= {col} <= 100").sort_values(col, ascending=False).reset_index(drop=True)
    else:
        data = df_work.dropna().sort_values(col, ascending=False).reset_index(drop=True)
    if data.empty:
        return _empty_fig()

    # First bar (tallest) gets distinct color, rest all same color
    FIRST_COLOR = "#E15759"   # red/distinct for top continent
    OTHER_COLOR = "#4E79A7"   # blue for the rest
    bar_colors = [FIRST_COLOR] + [OTHER_COLOR] * (len(data) - 1)

    text_vals = [_fmt_percent(v) if is_pct else _fmt(v) for v in data[col]]
    fig = go.Figure(go.Bar(
        x=data["continent"], y=data[col],
        marker=dict(color=bar_colors, line=dict(color=COLOR_BORDER, width=1.2)),
        text=text_vals, textposition="outside",
        textfont=dict(color=COLOR_TEXT, size=12),
        hovertemplate=f"<b>%{{x}}</b><br>{y_label}: %{{y:,.1f}}<extra></extra>",
        showlegend=False,
    ))
    layout = _m3_base_layout(title, "Continent", y_label, height=580, show_legend=False)
    layout["yaxis"]["range"] = y_range if y_range else [0, data[col].max() * 1.2]
    fig.update_layout(**layout)
    return fig


def m3_cases_per_million(df):
    return _m3_continent_bar(df, "avg_cases_per_million", COLOR_CASES,
                             "Average Cases per Million — by Continent", "Cases per Million")

def m3_deaths_per_million(df):
    return _m3_continent_bar(df, "avg_deaths_per_million", COLOR_DEATHS,
                             "Average Deaths per Million — by Continent", "Deaths per Million")

def m3_vaccination_rate(df):
    return _m3_continent_bar(df, "avg_vaccination_rate", COLOR_VACCINATIONS,
                             "Average Vaccination Rate (%) — by Continent",
                             "Vaccination Rate (%)", y_range=[0, 100], is_pct=True)


# ══════════════════════════════════════════════════════════════════════════════
# MEMBER 3 — CHART 4-1: Histogram
# ══════════════════════════════════════════════════════════════════════════════
def m3_histogram(df, n_bins=30):
    try:
        n_bins = int(n_bins) if n_bins else 30
    except (ValueError, TypeError):
        n_bins = 30
    
    if "total_cases" not in df.columns:
        return _empty_fig()
    vals = pd.to_numeric(df["total_cases"], errors="coerce").dropna()
    vals = vals[vals >= 1_000]
    if len(vals) < 5:
        return _empty_fig("Insufficient data")

    vals_log = np.log10(vals)
    counts, bin_edges = np.histogram(vals_log, bins=n_bins)
    peak_idx    = int(counts.argmax())
    peak_center = (bin_edges[peak_idx] + bin_edges[peak_idx + 1]) / 2
    peak_start  = 10 ** bin_edges[peak_idx]
    peak_end    = 10 ** bin_edges[peak_idx + 1]
    peak_count  = int(counts[peak_idx])
    range_label = f"{_fmt(peak_start, 0)} – {_fmt(peak_end, 0)}"

    fig = go.Figure(go.Histogram(
        x=vals_log, nbinsx=n_bins,
        marker=dict(color=COLOR_CASES, line=dict(color=COLOR_BORDER, width=0.8)),
        hovertemplate="Log10: %{x:.2f}<br>Countries: %{y}<extra></extra>",
        showlegend=False,
    ))
    fig.add_annotation(
        x=peak_center, y=peak_count,
        text=f"<b>Peak: {peak_count} countries</b><br>({range_label} cases)",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
        arrowcolor=COLOR_CASES, font=dict(color=COLOR_TEXT, size=11),
        bgcolor="rgba(255,255,255,0.95)", bordercolor=COLOR_CASES,
        borderwidth=1.5, borderpad=8, yshift=20,
    )
    layout = _m3_base_layout(
        "Distribution of Total COVID-19 Cases Across Countries",
        "Total Cases (Log Scale, starting 1K)", "Number of Countries",
        height=600, show_legend=False,
    )
    fig.update_layout(**layout)
    tick_vals  = [1_000, 10_000, 100_000, 1_000_000, 10_000_000, 100_000_000]
    tick_texts = ["1K",  "10K",  "100K",  "1M",       "10M",      "100M"]
    x_max = vals_log.max()
    filtered = [(np.log10(v), t) for v, t in zip(tick_vals, tick_texts) if np.log10(v) <= x_max + 0.1]
    if filtered:
        tv, tt = zip(*filtered)
        fig.update_xaxes(tickvals=list(tv), ticktext=list(tt),
                         range=[np.log10(1_000) - 0.1, x_max + 0.2])
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MEMBER 3 — CHART 4-2: Box CFR
# ══════════════════════════════════════════════════════════════════════════════
def m3_box_cfr(df):
    if "case_fatality_rate" not in df.columns or "continent" not in df.columns:
        return _empty_fig()
    data = df[["continent", "case_fatality_rate"]].copy()
    data["case_fatality_rate"] = pd.to_numeric(data["case_fatality_rate"], errors="coerce")
    data = data.dropna().query("case_fatality_rate >= 0")
    if data.empty:
        return _empty_fig()
    medians = data.groupby("continent")["case_fatality_rate"].median().sort_values(ascending=False)
    fig = go.Figure()
    for cont in medians.index:
        subset     = data.loc[data["continent"] == cont, "case_fatality_rate"]
        median_val = float(subset.median())
        fig.add_trace(go.Box(
            y=subset, name=cont,
            marker=dict(color=COLOR_DEATHS, size=5),
            fillcolor=COLOR_GRAY_LIGHT,
            line=dict(color=COLOR_BORDER, width=1.5),
            boxpoints="outliers",
            hovertemplate=f"<b>{cont}</b><br>CFR: %{{y:.2f}}%<extra></extra>",
            showlegend=False,
        ))
        fig.add_annotation(
            x=cont, y=median_val,
            text=f"<b>{median_val:.2f}%</b>",
            showarrow=False, font=dict(color=COLOR_TEXT, size=11),
            yshift=28, bgcolor="rgba(255,255,255,0.9)",
            bordercolor=COLOR_BORDER, borderwidth=0.5,
        )
    layout = _m3_base_layout("Case Fatality Rate (%) Variation by Continent",
                             "Continent", "Case Fatality Rate (%)",
                             y_zero=True, height=600, show_legend=False)
    fig.update_layout(**layout)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MEMBER 3 — CHART 4-3: Violin Vax
# ══════════════════════════════════════════════════════════════════════════════
def m3_violin_vax(df):
    if "vaccination_rate_pct" not in df.columns or "continent" not in df.columns:
        return _empty_fig()
    data = df[["continent", "vaccination_rate_pct"]].copy()
    data["vaccination_rate_pct"] = pd.to_numeric(data["vaccination_rate_pct"], errors="coerce")
    data = data.dropna().query("0 <= vaccination_rate_pct <= 100")
    if data.empty:
        return _empty_fig()
    medians = data.groupby("continent")["vaccination_rate_pct"].median().sort_values(ascending=False)
    fig = go.Figure()
    for cont in medians.index:
        subset     = data.loc[data["continent"] == cont, "vaccination_rate_pct"]
        median_val = float(subset.median())
        fig.add_trace(go.Violin(
            y=subset, name=cont,
            fillcolor=COLOR_CASES_LIGHT, opacity=0.85,
            line_color=COLOR_BORDER, points=False,
            meanline_visible=False, box_visible=True,
            box_fillcolor="white", box_line_color=COLOR_BORDER,
            hovertemplate=f"<b>{cont}</b><br>Vax Rate: %{{y:.1f}}%<extra></extra>",
            showlegend=False,
        ))
        fig.add_annotation(
            x=cont, y=median_val,
            text=f"<b>{median_val:.1f}%</b>",
            showarrow=False, font=dict(color=COLOR_TEXT, size=11, family="Arial"),
            yshift=28, bgcolor="rgba(255,255,255,0.95)",
            bordercolor=COLOR_BORDER, borderwidth=0.5,
        )
    layout = _m3_base_layout("Vaccination Rate (%) Distribution by Continent",
                             "Continent", "Vaccination Rate (%)",
                             y_zero=True, height=600, show_legend=False)
    layout["yaxis"]["range"] = [0, 100]
    fig.update_layout(**layout)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MEMBER 4 — Relationship charts
# ══════════════════════════════════════════════════════════════════════════════
def _apply_m4_style(fig, title, x_title, y_title, y_zero=True):
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(size=18)),
        template="plotly_white", plot_bgcolor="white", paper_bgcolor="white",
        font=dict(size=13), margin=dict(l=80, r=50, t=90, b=80),
        legend=dict(title="Continent", orientation="v", x=0.98, y=0.98,
                    xanchor="right", yanchor="top",
                    bgcolor="rgba(255,255,255,0.9)", bordercolor="black", borderwidth=1),
        shapes=[dict(type="rect", xref="paper", yref="paper",
                     x0=0, y0=0, x1=1, y1=1,
                     line=dict(color="black", width=1.5), fillcolor="rgba(0,0,0,0)")],
    )
    fig.update_xaxes(title=x_title, showgrid=True, gridcolor="lightgray",
                     zeroline=True, zerolinecolor="black", ticks="outside", tickangle=0)
    fig.update_yaxes(title=y_title, showgrid=True, gridcolor="lightgray",
                     zeroline=True, zerolinecolor="black", ticks="outside", tickangle=0)
    if y_zero:
        fig.update_yaxes(rangemode="tozero")
    return fig


def m4_gdp_vs_cases(df):
    data = df.dropna(subset=[c for c in ["gdp_per_capita", "cases_per_million", "location", "continent"] if c in df.columns])
    if data.empty or "gdp_per_capita" not in data.columns or "cases_per_million" not in data.columns:
        return _empty_fig()
    fig = px.scatter(data, x="gdp_per_capita", y="cases_per_million",
                     color="continent", color_discrete_map=M4_CONTINENT_COLORS,
                     hover_name="location" if "location" in data.columns else None,
                     log_x=True, height=550)
    fig.update_traces(marker=dict(size=7, opacity=0.75, line=dict(width=1, color="black")),
                      hovertemplate="<b>%{hovertext}</b><br>GDP: $%{x:,.0f}<br>Cases/M: %{y:,.0f}<extra></extra>")
    return _apply_m4_style(fig, "GDP per Capita vs COVID-19 Cases per Million",
                           "GDP per Capita (USD, log scale)", "Cases per Million")


def m4_pop_vs_deaths(df):
    data = df.dropna(subset=[c for c in ["population", "total_deaths", "location", "continent"] if c in df.columns])
    if data.empty or "population" not in data.columns or "total_deaths" not in data.columns:
        return _empty_fig()
    fig = px.scatter(data, x="population", y="total_deaths",
                     color="continent", color_discrete_map=M4_CONTINENT_COLORS,
                     hover_name="location" if "location" in data.columns else None,
                     log_x=True, height=550)
    fig.update_traces(marker=dict(size=7, opacity=0.75, line=dict(width=1, color="black")),
                      hovertemplate="<b>%{hovertext}</b><br>Population: %{x:,.0f}<br>Deaths: %{y:,.0f}<extra></extra>")
    return _apply_m4_style(fig, "Population Size vs Total COVID-19 Deaths",
                           "Population (log scale)", "Total Deaths")


def m4_gdp_vs_vax_bubble(df):
    need = ["gdp_per_capita", "vaccination_rate_pct", "population", "location", "continent"]
    data = df.dropna(subset=[c for c in need if c in df.columns])
    if data.empty or not all(c in data.columns for c in ["gdp_per_capita", "vaccination_rate_pct", "population"]):
        return _empty_fig()
    data = data[data["population"] > 0].copy()
    fig = px.scatter(data, x="gdp_per_capita", y="vaccination_rate_pct",
                     color="continent", color_discrete_map=M4_CONTINENT_COLORS,
                     size="population", size_max=35,
                     hover_name="location" if "location" in data.columns else None,
                     log_x=True, height=580)
    fig.update_traces(marker=dict(sizemode="area", opacity=0.65, line=dict(width=1, color="black")),
                      hovertemplate="<b>%{hovertext}</b><br>GDP: $%{x:,.0f}<br>Vax Rate: %{y:.1f}%<extra></extra>")
    return _apply_m4_style(fig, "GDP per Capita vs Vaccination Rate",
                           "GDP per Capita (USD, log scale)", "Vaccination Rate (%)")


# ══════════════════════════════════════════════════════════════════════════════
# MEMBER 4 — Time-Series Charts
# ══════════════════════════════════════════════════════════════════════════════
def m4_global_cases_line(ts_json):
    if not ts_json:
        return _empty_fig("💡 حمّل ملف OWID الكامل للحصول على الرسوم الزمنية")
    ts = pd.read_json(io.StringIO(ts_json))
    if "date" not in ts.columns:
        return _empty_fig()
    ts["date"] = pd.to_datetime(ts["date"], errors="coerce")
    ts = ts.sort_values("date")
    fig = go.Figure()
    if "new_cases" in ts.columns:
        cdf = ts.dropna(subset=["new_cases"])
        fig.add_trace(go.Scatter(x=cdf["date"], y=cdf["new_cases"], name="Daily Cases",
                                 mode="lines", line=dict(color="rgba(99,110,250,0.2)", width=1),
                                 hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Daily Cases: %{y:,.0f}<extra></extra>"))
    if "cases_7day_ma" in ts.columns:
        mdf = ts.dropna(subset=["cases_7day_ma"])
        fig.add_trace(go.Scatter(x=mdf["date"], y=mdf["cases_7day_ma"], name="7-Day Average",
                                 mode="lines", line=dict(color="rgb(99,110,250)", width=3),
                                 hovertemplate="<b>%{x|%Y-%m-%d}</b><br>7-Day Avg: %{y:,.0f}<extra></extra>"))
    fig.update_layout(template="plotly_white", height=480,
                      title=dict(text="Global New Cases Over Time", x=0.5, xanchor="center",
                                 font=dict(size=18, color="#333333")),
                      xaxis_title="Date", yaxis_title="New Cases",
                      font=dict(size=12, family="Arial"), hovermode="x unified",
                      margin=dict(l=80, r=50, t=100, b=80),
                      xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                      yaxis=dict(showgrid=True, gridcolor="#f0f0f0"))
    return fig


def m4_global_vax_area(ts_json):
    if not ts_json:
        return _empty_fig("💡 حمّل ملف OWID الكامل")
    ts = pd.read_json(io.StringIO(ts_json))
    if "date" not in ts.columns:
        return _empty_fig()
    ts["date"] = pd.to_datetime(ts["date"], errors="coerce")
    ts = ts.sort_values("date")
    col = "new_vaccinations_7day_ma" if "new_vaccinations_7day_ma" in ts.columns else "new_vaccinations"
    if col not in ts.columns:
        return _empty_fig("No vaccination data available")
    fig = go.Figure(go.Scatter(x=ts["date"], y=ts[col], fill="tozeroy",
                               fillcolor="rgba(99,110,250,0.3)",
                               line=dict(color="rgb(99,110,250)", width=2),
                               name="Vaccinations (7-day avg)",
                               hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Vaccinations: %{y:,.0f}<extra></extra>"))
    fig.update_layout(template="plotly_white", height=460,
                      title=dict(text="Global Vaccination Trends Over Time", x=0.5, xanchor="center",
                                 font=dict(size=18, color="#333333")),
                      xaxis_title="Date", yaxis_title="New Vaccinations (7-day average)",
                      font=dict(size=12, family="Arial"), hovermode="x unified",
                      margin=dict(l=80, r=50, t=100, b=80),
                      xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                      yaxis=dict(showgrid=True, gridcolor="#f0f0f0"), showlegend=False)
    return fig


def m4_continent_cases_line(cont_ts_json):
    if not cont_ts_json:
        return _empty_fig("💡 حمّل ملف OWID الكامل")
    ts = pd.read_json(io.StringIO(cont_ts_json))
    if "date" not in ts.columns or "continent" not in ts.columns:
        return _empty_fig()
    ts["date"] = pd.to_datetime(ts["date"], errors="coerce")
    col = "new_cases_7day_ma" if "new_cases_7day_ma" in ts.columns else "new_cases"
    if col not in ts.columns:
        return _empty_fig()
    fig = px.line(ts, x="date", y=col, color="continent", height=480)
    fig.update_traces(mode="lines", line=dict(width=2))
    fig.update_layout(template="plotly_white",
                      title=dict(text="New Cases by Continent Over Time (7-Day Average)",
                                 x=0.5, xanchor="center", font=dict(size=18, color="#333333")),
                      xaxis_title="Date", yaxis_title="New Cases (7-day average)",
                      font=dict(size=12, family="Arial"), hovermode="x unified",
                      margin=dict(l=80, r=50, t=100, b=80),
                      xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                      yaxis=dict(showgrid=True, gridcolor="#f0f0f0"))
    return fig


def m4_continent_vax_line(cont_ts_json):
    if not cont_ts_json:
        return _empty_fig("💡 حمّل ملف OWID الكامل")
    ts = pd.read_json(io.StringIO(cont_ts_json))
    if "date" not in ts.columns or "continent" not in ts.columns:
        return _empty_fig()
    ts["date"] = pd.to_datetime(ts["date"], errors="coerce")
    col = "new_vaccinations_7day_ma" if "new_vaccinations_7day_ma" in ts.columns else "new_vaccinations"
    if col not in ts.columns:
        return _empty_fig()
    fig = px.line(ts, x="date", y=col, color="continent", height=480)
    fig.update_traces(mode="lines", line=dict(width=2))
    fig.update_layout(template="plotly_white",
                      title=dict(text="Vaccination Trends by Continent Over Time (7-Day Average)",
                                 x=0.5, xanchor="center", font=dict(size=18, color="#333333")),
                      xaxis_title="Date", yaxis_title="New Vaccinations (7-day average)",
                      font=dict(size=12, family="Arial"), hovermode="x unified",
                      margin=dict(l=80, r=50, t=100, b=80),
                      xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                      yaxis=dict(showgrid=True, gridcolor="#f0f0f0"))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MEMBER 5 — WEEK 2 Comparisons
# ══════════════════════════════════════════════════════════════════════════════
def update_comparisons(store_json, continents, view):
    try:
        if not store_json:
            return [_empty_fig()] * 4
        df = pd.read_json(io.StringIO(store_json))
        df = _ensure_columns(df)
        
        # Ensure continent column is string type
        if "continent" in df.columns:
            df["continent"] = df["continent"].astype(str).str.strip()
        
        continents = _ensure_continents_list(continents)
        if continents and "continent" in df.columns:
            # Convert continents list to list of strings
            continents_list = [str(c).strip() for c in continents]
            df = df[df["continent"].isin(continents_list)]

        # Only Cases + Vaccinations (no Deaths)
        STACK_METRICS_STACKED   = {}
        STACK_METRICS_CLUSTERED = {}
        for col, lbl in [("total_cases", "Cases"), ("total_vaccinations", "Vaccinations")]:
            if col in df.columns:
                STACK_METRICS_STACKED[lbl]   = col
                STACK_METRICS_CLUSTERED[lbl] = col
        if not STACK_METRICS_STACKED:
            return [_empty_fig("Insufficient columns")] * 4

        agg_df = (df[df["continent"] != "Unknown"]
                  .groupby("continent")[[*STACK_METRICS_STACKED.values()]]
                  .sum().reset_index())

        # For stacked: Vaccinations (biggest) gets distinct color, Cases gets same color
        STACKED_COLORS = {
            "Vaccinations": "#A32D2D",   # red  — biggest bar (dominant)
            "Cases":        "#185FA5",   # blue — smaller bar
        }
        # For clustered: same scheme
        CLUSTERED_COLORS = STACKED_COLORS.copy()

        BORDER_SHAPE = dict(type="rect", xref="paper", yref="paper",
                            x0=0, y0=0, x1=1, y1=1,
                            line=dict(color=COLOR_BORDER, width=2),
                            fillcolor="rgba(0,0,0,0)")

        LEGEND_TOP_RIGHT = dict(
            orientation="h", x=1, y=1.12,
            xanchor="right", yanchor="bottom",
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor=COLOR_BORDER, borderwidth=1,
        )

        def _build(metrics_dict, color_map, barmode, horiz=False, title=""):
            fig = go.Figure()
            for lbl, col in metrics_dict.items():
                c = color_map.get(lbl, "#888")
                kw = dict(name=lbl,
                          marker=dict(color=c, opacity=0.85,
                                      line=dict(color=COLOR_BORDER, width=1.0)))
                if horiz:
                    fig.add_trace(go.Bar(x=agg_df[col], y=agg_df["continent"], orientation="h", **kw))
                else:
                    fig.add_trace(go.Bar(x=agg_df["continent"], y=agg_df[col], **kw))
            axis_style = dict(linecolor=COLOR_BORDER, linewidth=2, mirror=True, showline=True)
            fig.update_layout(**CHART_LAYOUT, barmode=barmode, height=420,
                              title=title,
                              legend=LEGEND_TOP_RIGHT,
                              showlegend=True,
                              xaxis=dict(showgrid=True, gridcolor="#eee", **axis_style),
                              yaxis=dict(showgrid=True, gridcolor="#eee", **axis_style),
                              shapes=[BORDER_SHAPE])
            return fig

        fig_sc = _build(STACK_METRICS_STACKED,   STACKED_COLORS,   "stack", False,
                        "Stacked Column — Cases / Vaccinations by Continent")
        fig_sb = _build(STACK_METRICS_STACKED,   STACKED_COLORS,   "stack", True,
                        "Stacked Bar — Cases / Vaccinations by Continent")
        fig_cc = _build(STACK_METRICS_CLUSTERED, CLUSTERED_COLORS, "group", False,
                        "Clustered Column — Cases / Vaccinations by Continent")
        fig_cb = _build(STACK_METRICS_CLUSTERED, CLUSTERED_COLORS, "group", True,
                        "Clustered Bar — Cases / Vaccinations by Continent")
        return fig_sc, fig_sb, fig_cc, fig_cb
    except Exception as e:
        print(f"Error in update_comparisons: {e}")
        import traceback
        traceback.print_exc()
        return [_empty_fig()] * 4


# ══════════════════════════════════════════════════════════════════════════════
# DATA TABLE
# ══════════════════════════════════════════════════════════════════════════════
def update_table(store_json, continents, metric, view, search):
    if not store_json:
        return [], []
    df = pd.read_json(io.StringIO(store_json))
    df = _ensure_columns(df)
    
    # Ensure continent column is string type
    if "continent" in df.columns:
        df["continent"] = df["continent"].astype(str).str.strip()
    
    continents = _ensure_continents_list(continents)
    if continents and "continent" in df.columns:
        # Convert continents list to list of strings
        continents_list = [str(c).strip() for c in continents]
        df = df[df["continent"].isin(continents_list)]
    if search:
        df = df[df["location"].str.contains(search, case=False, na=False)]
    want = [c for c in ["location", "continent", "total_cases", "total_deaths",
                         "cases_per_million", "deaths_per_million", "case_fatality_rate",
                         "vaccination_rate_pct", "gdp_per_capita", "population"] if c in df.columns]
    LABEL = {
        "location": "Country", "continent": "Continent", "total_cases": "Total Cases",
        "total_deaths": "Total Deaths", "cases_per_million": "Cases/Million",
        "deaths_per_million": "Deaths/Million", "case_fatality_rate": "CFR %",
        "vaccination_rate_pct": "Vax %", "gdp_per_capita": "GDP/Capita",
        "population": "Population",
    }
    out = df[want].copy()
    # Determine sort column safely
    sort_col = metric if (metric and metric in want) else (want[2] if len(want) > 2 else want[0])
    try:
        out = out.sort_values(sort_col, ascending=False).head(100)
    except Exception:
        out = out.head(100)
    for c in out.columns:
        if out[c].dtype in [float, np.float64]:
            out[c] = out[c].apply(
                lambda x: (f"{x:.2f}%" if "rate" in c or "pct" in c else fmt(x)) if pd.notna(x) else "—"
            )
    return out.to_dict("records"), [{"name": LABEL.get(c, c), "id": c} for c in want]


# ══════════════════════════════════════════════════════════════════════════════
# REGISTER CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════
def register_callbacks(app):

    # ── AUTO-LOAD DATA ON PAGE LOAD ───────────────────────────────────────────
    @app.callback(
        Output("btn-load", "n_clicks"),
        Input("interval-autoload", "n_intervals"),
    )
    def auto_load_on_startup(n_intervals):
        """Auto-load data when page loads (triggered by interval)"""
        if n_intervals and n_intervals >= 1:
            return 1  # Trigger the load button once
        return no_update

    # ── CB-LOAD ───────────────────────────────────────────────────────────────
    @app.callback(
        Output("store-country",    "data"),
        Output("store-timeseries", "data"),
        Output("store-cont-ts",    "data"),
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
    def cb_load(n, path):
        if not path:
            raise PreventUpdate
        try:
            raw = _load_csv(path)
            is_full = ("iso_code" in raw.columns and "date" in raw.columns and len(raw) > 5_000)
            ts_json = cont_ts_json = None
            if is_full:
                global_ts, cont_ts = _build_timeseries(path)
                if global_ts is not None:
                    ts_json = global_ts.to_json(date_format="iso")
                if cont_ts is not None:
                    cont_ts_json = cont_ts.to_json(date_format="iso")
                raw = _process_owid(raw)
            df = _ensure_columns(raw)
            country_json = df.to_json(date_format="iso")
            n_c  = len(df)
            tc   = df["total_cases"].sum()         if "total_cases"         in df.columns else 0
            td   = df["total_deaths"].sum()        if "total_deaths"        in df.columns else 0
            tv   = df["total_vaccinations"].sum()  if "total_vaccinations"  in df.columns else 0
            cfr  = (td / tc * 100) if tc > 0 else 0
            vp   = df["vaccination_rate_pct"].mean() if "vaccination_rate_pct" in df.columns else float("nan")
            ts_label = "With time-series data ✔" if ts_json else "No time-series data"
            status = f"✅ Loaded {n_c:,} countries  ·  {ts_label}"
            return (country_json, ts_json, cont_ts_json, status,
                    f"{n_c:,}", fmt(tc), fmt(td), fmt(tv),
                    f"{cfr:.2f}%",
                    f"{vp:.1f}%" if not np.isnan(vp) else "—",
                    f"📊 {n_c:,} countries")
        except Exception as e:
            return (no_update,) * 10 + (f"❌ Error: {e}",)

    def _get_df(store_json, continents):
        if not store_json:
            return None
        df = pd.read_json(io.StringIO(store_json))
        df = _ensure_columns(df)
        
        # Ensure continent column is string type
        if "continent" in df.columns:
            df["continent"] = df["continent"].astype(str).str.strip()
        
        continents = _ensure_continents_list(continents)
        if continents and "continent" in df.columns:
            # Convert continents list to list of strings
            continents = [str(c).strip() for c in continents]
            df = df[df["continent"].isin(continents)]
        return df

    # ── M5 Overview ───────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-column", "figure"), Output("chart-bar", "figure"),
        Input("store-country", "data"), Input("dd-continent", "value"),
        Input("dd-metric", "value"), Input("radio-view", "value"), Input("slider-topn", "value"),
    )
    def cb_overview(s, c, m, v, n):
        try:
            return update_overview(s, c, m, v, n)
        except Exception as e:
            print(f"Error in cb_overview: {e}")
            import traceback
            traceback.print_exc()
            return _empty_fig(), _empty_fig()

    # ── M5 Comparisons ────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-stacked-col", "figure"), Output("chart-stacked-bar", "figure"),
        Output("chart-cluster-col", "figure"), Output("chart-cluster-bar", "figure"),
        Input("store-country", "data"), Input("dd-continent", "value"), Input("radio-view", "value"),
    )
    def cb_comparisons(s, c, v):
        try:
            return update_comparisons(s, c, v)
        except Exception as e:
            print(f"Error in cb_comparisons: {e}")
            import traceback
            traceback.print_exc()
            return [_empty_fig()] * 4

    # ── M3 Top N ──────────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-m3-top10", "figure"),
        Input("store-country", "data"), Input("dd-continent", "value"), Input("slider-topn", "value"),
    )
    def cb_m3_top10(s, c, n):
        df = _get_df(s, c)
        return m3_top10_cases(df, top_n=n) if df is not None else _empty_fig()

    # ── M3 Deaths by Continent ────────────────────────────────────────────────
    @app.callback(
        Output("chart-m3-deaths-cont", "figure"),
        Input("store-country", "data"), Input("dd-continent", "value"),
    )
    def cb_m3_deaths(s, c):
        df = _get_df(s, c)
        return m3_deaths_by_continent(df) if df is not None else _empty_fig()

    # ── M3 100% Stacked ───────────────────────────────────────────────────────
    @app.callback(
        Output("chart-m3-stacked-pct", "figure"),
        Input("store-country", "data"), Input("dd-continent", "value"),
    )
    def cb_m3_stacked(s, c):
        df = _get_df(s, c)
        return m3_stacked_pct(df) if df is not None else _empty_fig()

    # ── M3 Grouped Log ────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-m3-grouped-log", "figure"),
        Input("store-country", "data"), Input("dd-continent", "value"),
    )
    def cb_m3_grouped(s, c):
        df = _get_df(s, c)
        return m3_grouped_log(df) if df is not None else _empty_fig()

    # ── M3 Normalised bars ────────────────────────────────────────────────────
    @app.callback(
        Output("chart-m3-cpm", "figure"),
        Output("chart-m3-dpm", "figure"),
        Output("chart-m3-vaxpct", "figure"),
        Input("store-country", "data"), Input("dd-continent", "value"),
    )
    def cb_m3_norm(s, c):
        df = _get_df(s, c)
        if df is None:
            return _empty_fig(), _empty_fig(), _empty_fig()
        return m3_cases_per_million(df), m3_deaths_per_million(df), m3_vaccination_rate(df)

    # ── M3 Histogram ──────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-m3-hist", "figure"),
        Input("store-country", "data"), Input("dd-continent", "value"),
    )
    def cb_m3_hist(s, c):
        df = _get_df(s, c)
        return m3_histogram(df) if df is not None else _empty_fig()

    # ── M3 Box ────────────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-m3-box", "figure"),
        Input("store-country", "data"), Input("dd-continent", "value"),
    )
    def cb_m3_box(s, c):
        df = _get_df(s, c)
        return m3_box_cfr(df) if df is not None else _empty_fig()

    # ── M3 Violin ─────────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-m3-violin", "figure"),
        Input("store-country", "data"), Input("dd-continent", "value"),
    )
    def cb_m3_violin(s, c):
        df = _get_df(s, c)
        return m3_violin_vax(df) if df is not None else _empty_fig()

    # ── M4 GDP vs Cases ───────────────────────────────────────────────────────
    @app.callback(
        Output("chart-m4-gdp-cases", "figure"),
        Input("store-country", "data"), Input("dd-continent", "value"),
    )
    def cb_m4_gdp_cases(s, c):
        df = _get_df(s, c)
        return m4_gdp_vs_cases(df) if df is not None else _empty_fig()

    # ── M4 Pop vs Deaths ──────────────────────────────────────────────────────
    @app.callback(
        Output("chart-m4-pop-deaths", "figure"),
        Input("store-country", "data"), Input("dd-continent", "value"),
    )
    def cb_m4_pop_deaths(s, c):
        df = _get_df(s, c)
        return m4_pop_vs_deaths(df) if df is not None else _empty_fig()

    # ── M4 Bubble ─────────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-m4-bubble", "figure"),
        Input("store-country", "data"), Input("dd-continent", "value"),
    )
    def cb_m4_bubble(s, c):
        df = _get_df(s, c)
        return m4_gdp_vs_vax_bubble(df) if df is not None else _empty_fig()

    # ── M4 Global Cases Line ──────────────────────────────────────────────────
    @app.callback(Output("chart-m4-global-cases", "figure"), Input("store-timeseries", "data"))
    def cb_m4_global_cases(ts): return m4_global_cases_line(ts)

    # ── M4 Global Vax Area ────────────────────────────────────────────────────
    @app.callback(Output("chart-m4-global-vax", "figure"), Input("store-timeseries", "data"))
    def cb_m4_global_vax(ts): return m4_global_vax_area(ts)

    # ── M4 Continent Cases ────────────────────────────────────────────────────
    @app.callback(Output("chart-m4-cont-cases", "figure"), Input("store-cont-ts", "data"))
    def cb_m4_cont_cases(cts): return m4_continent_cases_line(cts)

    # ── M4 Continent Vax ──────────────────────────────────────────────────────
    @app.callback(Output("chart-m4-cont-vax", "figure"), Input("store-cont-ts", "data"))
    def cb_m4_cont_vax(cts): return m4_continent_vax_line(cts)

    # ── Data Table ────────────────────────────────────────────────────────────
    @app.callback(
        Output("data-table", "data"), Output("data-table", "columns"),
        Input("store-country", "data"), Input("dd-continent", "value"),
        Input("dd-metric", "value"), Input("radio-view", "value"), Input("table-search", "value"),
    )
    def cb_table(s, c, m, v, search): return update_table(s, c, m, v, search)

    # ── Export CSV ────────────────────────────────────────────────────────────
    @app.callback(
        Output("download-csv", "data"),
        Input("btn-export", "n_clicks"),
        State("store-country", "data"), State("dd-continent", "value"),
        prevent_initial_call=True,
    )
    def cb_export(n, s, c):
        if not s:
            raise PreventUpdate
        df = pd.read_json(io.StringIO(s))
        df = _ensure_columns(df)
        
        # Ensure continent column is string type
        if "continent" in df.columns:
            df["continent"] = df["continent"].astype(str).str.strip()
        
        c = _ensure_continents_list(c)
        if c and "continent" in df.columns:
            # Convert continents list to list of strings
            c_list = [str(x).strip() for x in c]
            df = df[df["continent"].isin(c_list)]
        return dcc.send_data_frame(df.to_csv, "covid19_filtered.csv",
                                   index=False, encoding="utf-8-sig")
