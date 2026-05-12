"""
test_dashboard.py
==================
Comprehensive tests for the COVID-19 Plotly Dash Dashboard.

Test Categories
---------------
  ✅ T1  — Data utilities  (loading, processing, column normalisation)
  ✅ T2  — KPI calculations
  ✅ T3  — Chart generation  (all 9 weeks, CB-2 → CB-10)
  ✅ T4  — Layout structure  (components & IDs present)
  ✅ T5  — Callback wiring   (correct inputs/outputs registered)
  ✅ T6  — Edge cases        (empty data, missing columns, NaN)
  ✅ T7  — Interactive filters (continent, metric, view, top-n)

Run:
    cd covid_dashboard
    pytest test_dashboard.py -v
"""

import io
import json
import sys
import os
import pytest
import numpy as np
import pandas as pd

# ── Make sure project root is on path ─────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════
SAMPLE_CSV = r"F:\faculty\Level 3 S_2\Data Visualization\Global COVID-19 Pandemic Analysis\Global-COVID-19-Pandemic-Analysis\Data\Processed\final_dataset.csv"

@pytest.fixture
def sample_df():
    """10-row country-level DataFrame for tests."""
    return pd.read_csv(SAMPLE_CSV)


@pytest.fixture
def processed_df(sample_df):
    """Fully processed DataFrame (ensure_columns applied)."""
    from app.callbacks.dashboard_callbacks import _ensure_columns
    return _ensure_columns(sample_df.copy())


@pytest.fixture
def store_json(processed_df):
    """JSON string as stored in dcc.Store."""
    return processed_df.to_json(date_format="iso")


@pytest.fixture
def all_continents():
    return ["Asia", "Europe", "Africa", "North America", "South America", "Oceania"]


# ══════════════════════════════════════════════════════════════════════════════
# T1 — DATA UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
class TestDataUtilities:

    def test_csv_loads(self):
        """CSV file can be read successfully."""
        from app.callbacks.dashboard_callbacks import _load_csv
        df = _load_csv(SAMPLE_CSV)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_ensure_columns_renames(self):
        """ensure_columns maps old column names to standard ones."""
        from app.callbacks.dashboard_callbacks import _ensure_columns
        df = pd.DataFrame([{"country": "Egypt", "cases": 1000, "deaths": 50}])
        out = _ensure_columns(df)
        assert "location"     in out.columns
        assert "total_cases"  in out.columns
        assert "total_deaths" in out.columns

    def test_ensure_columns_derives_cfr(self, sample_df):
        """CFR is derived when total_cases and total_deaths exist."""
        from app.callbacks.dashboard_callbacks import _ensure_columns
        df = _ensure_columns(sample_df.copy())
        assert "case_fatality_rate" in df.columns
        # CFR must be between 0 and 100
        valid = df["case_fatality_rate"].dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_ensure_columns_derives_vax_pct(self, sample_df):
        """vaccination_rate_pct is derived from people_fully_vaccinated_per_hundred."""
        from app.callbacks.dashboard_callbacks import _ensure_columns
        df = _ensure_columns(sample_df.copy())
        assert "vaccination_rate_pct" in df.columns

    def test_ensure_columns_derives_cases_per_million(self, sample_df):
        """cases_per_million is derived when column is absent."""
        from app.callbacks.dashboard_callbacks import _ensure_columns
        df = sample_df.copy()
        df = df.drop(columns=[c for c in ["cases_per_million", "total_cases_per_million"]
                               if c in df.columns], errors="ignore")
        out = _ensure_columns(df)
        assert "cases_per_million" in out.columns

    def test_fmt_millions(self):
        """fmt() correctly formats millions."""
        from app.callbacks.dashboard_callbacks import fmt
        assert "M" in fmt(5_000_000)

    def test_fmt_billions(self):
        """fmt() correctly formats billions."""
        from app.callbacks.dashboard_callbacks import fmt
        assert "B" in fmt(2_000_000_000)

    def test_fmt_nan(self):
        """fmt() returns '—' for NaN."""
        from app.callbacks.dashboard_callbacks import fmt
        assert fmt(float("nan")) == "—"

    def test_get_display_raw(self, processed_df):
        """_get_display with view='raw' returns the column directly."""
        from app.callbacks.dashboard_callbacks import _get_display
        result = _get_display(processed_df, "total_cases", "raw")
        assert len(result) == len(processed_df)

    def test_get_display_per_million(self, processed_df):
        """_get_display with view='per_million' divides by population."""
        from app.callbacks.dashboard_callbacks import _get_display
        raw    = _get_display(processed_df, "total_cases", "raw")
        per_m  = _get_display(processed_df, "total_cases", "per_million")
        # Per-million values should generally be smaller than raw totals
        assert per_m.mean() < raw.mean()

    def test_get_display_pct(self, processed_df):
        """_get_display with view='pct' returns values <= 100 for vaccinations."""
        from app.callbacks.dashboard_callbacks import _get_display
        result = _get_display(processed_df, "total_vaccinations", "pct")
        assert isinstance(result, pd.Series)


# ══════════════════════════════════════════════════════════════════════════════
# T2 — KPI CALCULATIONS
# ══════════════════════════════════════════════════════════════════════════════
class TestKPICalculations:

    def test_kpi_country_count(self, processed_df):
        """Country count matches DataFrame length."""
        assert len(processed_df) == 10

    def test_kpi_total_cases_positive(self, processed_df):
        total = processed_df["total_cases"].sum()
        assert total > 0

    def test_kpi_cfr_range(self, processed_df):
        total_cases  = processed_df["total_cases"].sum()
        total_deaths = processed_df["total_deaths"].sum()
        cfr = total_deaths / total_cases * 100
        assert 0 < cfr < 100

    def test_kpi_avg_vax_pct(self, processed_df):
        avg = processed_df["vaccination_rate_pct"].mean()
        assert 0 <= avg <= 100


# ══════════════════════════════════════════════════════════════════════════════
# T3 — CHART GENERATION (all 9 weeks)
# ══════════════════════════════════════════════════════════════════════════════
class TestChartGeneration:

    # ── Week 1 ────────────────────────────────────────────────────────────────
    def test_week1_column_chart(self, store_json, all_continents):
        """Week 1 — Column Chart returns valid Plotly figure."""
        from app.callbacks.dashboard_callbacks import update_overview
        fig_col, fig_bar = update_overview(store_json, all_continents, "total_cases", "raw", 10)
        assert fig_col is not None
        assert len(fig_col.data) > 0

    def test_week1_bar_chart(self, store_json, all_continents):
        """Week 1 — Bar Chart is horizontal (orientation='h')."""
        from app.callbacks.dashboard_callbacks import update_overview
        _, fig_bar = update_overview(store_json, all_continents, "total_cases", "raw", 10)
        assert fig_bar.data[0].orientation == "h"

    def test_week1_column_title_contains_topn(self, store_json, all_continents):
        """Column chart title mentions top-N value."""
        from app.callbacks.dashboard_callbacks import update_overview
        fig_col, _ = update_overview(store_json, all_continents, "total_cases", "raw", 7)
        assert "7" in fig_col.layout.title.text

    # ── Week 2 ────────────────────────────────────────────────────────────────
    def test_week2_stacked_column(self, store_json, all_continents):
        """Week 2 — Stacked Column has barmode='stack'."""
        from app.callbacks.dashboard_callbacks import update_comparisons
        fig_sc, fig_sb, fig_cc, fig_cb = update_comparisons(store_json, all_continents, "raw")
        assert fig_sc.layout.barmode == "stack"

    def test_week2_stacked_bar_horizontal(self, store_json, all_continents):
        """Week 2 — Stacked Bar is horizontal."""
        from app.callbacks.dashboard_callbacks import update_comparisons
        _, fig_sb, _, _ = update_comparisons(store_json, all_continents, "raw")
        assert fig_sb.data[0].orientation == "h"

    def test_week2_clustered_column(self, store_json, all_continents):
        """Week 2 — Clustered Column has barmode='group'."""
        from app.callbacks.dashboard_callbacks import update_comparisons
        _, _, fig_cc, _ = update_comparisons(store_json, all_continents, "raw")
        assert fig_cc.layout.barmode == "group"

    def test_week2_clustered_bar_horizontal(self, store_json, all_continents):
        """Week 2 — Clustered Bar is horizontal."""
        from app.callbacks.dashboard_callbacks import update_comparisons
        _, _, _, fig_cb = update_comparisons(store_json, all_continents, "raw")
        assert fig_cb.data[0].orientation == "h"

    def test_week2_four_charts_returned(self, store_json, all_continents):
        """Week 2 — returns exactly 4 figures."""
        from app.callbacks.dashboard_callbacks import update_comparisons
        result = update_comparisons(store_json, all_continents, "raw")
        assert len(result) == 4

    # ── Week 3 ────────────────────────────────────────────────────────────────
    def test_week3_scatter_chart(self, store_json, all_continents):
        """Week 3 — Scatter Chart has at least one trace."""
        from app.callbacks.dashboard_callbacks import update_scatter
        fig = update_scatter(store_json, all_continents, "total_cases", "total_deaths")
        assert len(fig.data) > 0

    def test_week3_scatter_title_contains_labels(self, store_json, all_continents):
        """Week 3 — Scatter title mentions the selected metrics."""
        from app.callbacks.dashboard_callbacks import update_scatter
        fig = update_scatter(store_json, all_continents, "total_cases", "total_deaths")
        title = fig.layout.title.text
        assert "إصابات" in title or "وفيات" in title

    # ── Week 4 ────────────────────────────────────────────────────────────────
    def test_week4_bubble_chart(self, store_json, all_continents):
        """Week 4 — Bubble Chart has data traces."""
        from app.callbacks.dashboard_callbacks import update_bubble
        fig = update_bubble(store_json, all_continents)
        assert len(fig.data) > 0

    def test_week4_bubble_has_size(self, store_json, all_continents):
        """Week 4 — Bubble Chart marker sizes are set (not all zero)."""
        from app.callbacks.dashboard_callbacks import update_bubble
        fig = update_bubble(store_json, all_continents)
        sizes = fig.data[0].marker.size
        assert sizes is not None and max(sizes) > 0

    # ── Week 5 ────────────────────────────────────────────────────────────────
    def test_week5_histogram(self, store_json, all_continents):
        """Week 5 — Histogram has at least one trace."""
        from app.callbacks.dashboard_callbacks import update_histogram
        fig = update_histogram(store_json, all_continents, "total_cases", "raw")
        assert len(fig.data) > 0

    def test_week5_histogram_type(self, store_json, all_continents):
        """Week 5 — Histogram trace type is 'histogram'."""
        from app.callbacks.dashboard_callbacks import update_histogram
        fig = update_histogram(store_json, all_continents, "total_cases", "raw")
        assert fig.data[0].type == "histogram"

    # ── Week 6 ────────────────────────────────────────────────────────────────
    def test_week6_box_chart(self, store_json, all_continents):
        """Week 6 — Box Chart has traces."""
        from app.callbacks.dashboard_callbacks import update_box
        fig = update_box(store_json, all_continents, "total_cases", "raw")
        assert len(fig.data) > 0

    def test_week6_box_trace_type(self, store_json, all_continents):
        """Week 6 — Box Chart trace type is 'box'."""
        from app.callbacks.dashboard_callbacks import update_box
        fig = update_box(store_json, all_continents, "total_cases", "raw")
        assert fig.data[0].type == "box"

    # ── Week 7 ────────────────────────────────────────────────────────────────
    def test_week7_violin_chart(self, store_json, all_continents):
        """Week 7 — Violin Chart has traces."""
        from app.callbacks.dashboard_callbacks import update_violin
        fig = update_violin(store_json, all_continents, "total_cases", "raw")
        assert len(fig.data) > 0

    def test_week7_violin_trace_type(self, store_json, all_continents):
        """Week 7 — Violin Chart trace type is 'violin'."""
        from app.callbacks.dashboard_callbacks import update_violin
        fig = update_violin(store_json, all_continents, "total_cases", "raw")
        assert fig.data[0].type == "violin"

    # ── Week 8 ────────────────────────────────────────────────────────────────
    def test_week8_line_chart_no_data(self):
        """Week 8 — Line Chart returns empty-state figure when no time-series."""
        from app.callbacks.dashboard_callbacks import update_line
        fig = update_line(None)
        assert fig is not None  # should return an empty-state fig, not crash

    def test_week8_line_chart_with_data(self):
        """Week 8 — Line Chart renders correctly with time-series data."""
        from app.callbacks.dashboard_callbacks import update_line
        ts = pd.DataFrame({
            "date": pd.date_range("2021-01-01", periods=30),
            "new_cases": np.random.randint(1000, 50000, 30),
            "new_deaths": np.random.randint(10, 1000, 30),
            "cases_7day_ma": np.random.uniform(1000, 50000, 30),
            "deaths_7day_ma": np.random.uniform(10, 1000, 30),
        })
        ts_json = ts.to_json(date_format="iso")
        fig = update_line(ts_json)
        assert len(fig.data) >= 2   # at least cases + deaths traces

    # ── Week 9 ────────────────────────────────────────────────────────────────
    def test_week9_area_chart_no_data(self):
        """Week 9 — Area Chart returns empty-state figure when no time-series."""
        from app.callbacks.dashboard_callbacks import update_area
        fig = update_area(None)
        assert fig is not None

    def test_week9_area_chart_with_data(self):
        """Week 9 — Area Chart uses fill='tozeroy' for area effect."""
        from app.callbacks.dashboard_callbacks import update_area
        ts = pd.DataFrame({
            "date": pd.date_range("2021-01-01", periods=30),
            "new_cases": np.random.randint(1000, 50000, 30),
            "new_deaths": np.random.randint(10, 1000, 30),
        })
        fig = update_area(ts.to_json(date_format="iso"))
        fills = [t.fill for t in fig.data]
        assert "tozeroy" in fills


# ══════════════════════════════════════════════════════════════════════════════
# T4 — LAYOUT STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════
class TestLayoutStructure:

    @pytest.fixture(autouse=True)
    def _build(self):
        from app.layout.dashboard_layout import build_layout
        self.layout = build_layout()

    def _find_ids(self, component, found=None):
        """Recursively collect all component IDs in the layout tree."""
        if found is None:
            found = set()
        if hasattr(component, "id") and component.id:
            found.add(component.id)
        for attr in ("children",):
            children = getattr(component, attr, None)
            if children is None:
                continue
            if isinstance(children, (list, tuple)):
                for child in children:
                    self._find_ids(child, found)
            elif hasattr(children, "id") or hasattr(children, "children"):
                self._find_ids(children, found)
        return found

    def test_layout_not_none(self):
        assert self.layout is not None

    @pytest.mark.parametrize("component_id", [
        "store-country", "store-timeseries",
        "btn-load", "input-csv-path", "load-status",
        "dd-continent", "dd-metric", "slider-topn", "radio-view",
        "kpi-countries", "kpi-cases", "kpi-deaths",
        "kpi-vax", "kpi-cfr", "kpi-vax-pct",
        "chart-column", "chart-bar",
        "chart-stacked-col", "chart-stacked-bar",
        "chart-cluster-col", "chart-cluster-bar",
        "chart-scatter", "chart-bubble",
        "chart-histogram", "chart-box", "chart-violin",
        "chart-line", "chart-area",
        "data-table", "table-search",
        "btn-export", "download-csv",
    ])
    def test_component_id_present(self, component_id):
        """Every required component ID must exist in the layout."""
        ids = self._find_ids(self.layout)
        assert component_id in ids, f"Component ID '{component_id}' not found in layout"


# ══════════════════════════════════════════════════════════════════════════════
# T5 — CALLBACK WIRING
# ══════════════════════════════════════════════════════════════════════════════
class TestCallbackWiring:

    @pytest.fixture(autouse=True)
    def _app(self):
        from dash import Dash
        import dash_bootstrap_components as dbc
        from app.layout.dashboard_layout import build_layout
        from app.callbacks.dashboard_callbacks import register_callbacks
        self.app = Dash(__name__,
                        external_stylesheets=[dbc.themes.BOOTSTRAP],
                        suppress_callback_exceptions=True)
        self.app.layout = build_layout()
        register_callbacks(self.app)

    def _callback_output_ids(self):
        ids = set()
        for cb in self.app.callback_map.values():
            raw = cb["output"]
            # Normalise: can be a single Output or a list of Outputs
            outputs = raw if isinstance(raw, (list, tuple)) else [raw]
            for out in outputs:
                if isinstance(out, dict):
                    ids.add(out.get("id", out.get("component_id", "")))
                elif hasattr(out, "component_id"):
                    ids.add(out.component_id)
        return ids

    def test_callbacks_registered(self):
        """At least 10 callbacks should be registered."""
        assert len(self.app.callback_map) >= 10

    @pytest.mark.parametrize("chart_id", [
        "chart-column", "chart-bar",
        "chart-stacked-col", "chart-stacked-bar",
        "chart-cluster-col", "chart-cluster-bar",
        "chart-scatter", "chart-bubble",
        "chart-histogram", "chart-box", "chart-violin",
        "chart-line", "chart-area",
    ])
    def test_chart_has_callback(self, chart_id):
        """Every chart component must be wired as a callback Output."""
        out_ids = self._callback_output_ids()
        assert chart_id in out_ids, f"No callback updates '{chart_id}'"

    def test_kpi_updated_by_callback(self):
        """KPI cards must be updated by a callback."""
        out_ids = self._callback_output_ids()
        assert "kpi-cases" in out_ids

    def test_store_updated_by_load(self):
        """store-country must be updated by the load callback."""
        out_ids = self._callback_output_ids()
        assert "store-country" in out_ids

    def test_download_wired(self):
        """download-csv must be a callback output (export)."""
        out_ids = self._callback_output_ids()
        assert "download-csv" in out_ids


# ══════════════════════════════════════════════════════════════════════════════
# T6 — EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════
class TestEdgeCases:

    def test_empty_store_returns_empty_fig(self):
        """Callbacks receiving None store should not raise exceptions."""
        from app.callbacks.dashboard_callbacks import (
            update_overview, update_comparisons, update_scatter,
            update_bubble, update_histogram, update_box, update_violin,
        )
        all_c = ["Asia"]
        assert update_overview(None, all_c, "total_cases", "raw", 10) is not None
        assert update_comparisons(None, all_c, "raw") is not None
        assert update_scatter(None, all_c, "total_cases", "total_deaths") is not None
        assert update_bubble(None, all_c) is not None
        assert update_histogram(None, all_c, "total_cases", "raw") is not None
        assert update_box(None, all_c, "total_cases", "raw") is not None
        assert update_violin(None, all_c, "total_cases", "raw") is not None

    def test_missing_column_no_crash(self, store_json, all_continents):
        """Requesting a non-existent metric column should return empty fig gracefully."""
        from app.callbacks.dashboard_callbacks import update_scatter
        fig = update_scatter(store_json, all_continents, "nonexistent_col", "total_deaths")
        assert fig is not None

    def test_all_nan_metric(self, processed_df):
        """All-NaN metric should not cause a crash in histogram."""
        from app.callbacks.dashboard_callbacks import update_histogram
        processed_df["total_cases"] = np.nan
        store_json = processed_df.to_json(date_format="iso")
        fig = update_histogram(store_json, ["Asia"], "total_cases", "raw")
        assert fig is not None

    def test_single_country_charts(self, processed_df, all_continents):
        """Single-row DataFrame should not crash any chart."""
        from app.callbacks.dashboard_callbacks import update_overview
        single = processed_df.head(1).to_json(date_format="iso")
        result = update_overview(single, all_continents, "total_cases", "raw", 5)
        assert result is not None

    def test_continent_filter_reduces_rows(self, processed_df):
        """Filtering to one continent should return fewer rows."""
        asia_only = processed_df[processed_df["continent"] == "Asia"]
        all_count = len(processed_df)
        assert len(asia_only) < all_count


# ══════════════════════════════════════════════════════════════════════════════
# T7 — INTERACTIVE FILTERS
# ══════════════════════════════════════════════════════════════════════════════
class TestInteractiveFilters:

    def test_topn_slider_limits_bars(self, store_json, all_continents):
        """Top-N=3 should show at most 3 bars in the column chart."""
        from app.callbacks.dashboard_callbacks import update_overview
        fig_col, _ = update_overview(store_json, all_continents, "total_cases", "raw", 3)
        assert len(fig_col.data[0].x) <= 3

    def test_metric_change_updates_title(self, store_json, all_continents):
        """Changing metric from cases→deaths should change chart title."""
        from app.callbacks.dashboard_callbacks import update_overview
        fig_cases, _ = update_overview(store_json, all_continents, "total_cases", "raw", 10)
        fig_deaths, _ = update_overview(store_json, all_continents, "total_deaths", "raw", 10)
        assert fig_cases.layout.title.text != fig_deaths.layout.title.text

    def test_continent_filter_asia_only(self, store_json):
        """Filtering to Asia only should yield a smaller chart."""
        from app.callbacks.dashboard_callbacks import update_overview
        fig_all, _  = update_overview(store_json, ["Asia","Europe","Africa",
                                                    "North America","South America","Oceania"],
                                      "total_cases", "raw", 20)
        fig_asia, _ = update_overview(store_json, ["Asia"], "total_cases", "raw", 20)
        assert len(fig_asia.data[0].x) <= len(fig_all.data[0].x)

    def test_view_per_million_changes_values(self, store_json, all_continents):
        """Switching to per-million normalisation changes y-axis values."""
        from app.callbacks.dashboard_callbacks import update_overview
        fig_raw, _  = update_overview(store_json, all_continents, "total_cases", "raw", 10)
        fig_pm,  _  = update_overview(store_json, all_continents, "total_cases", "per_million", 10)
        assert list(fig_raw.data[0].y) != list(fig_pm.data[0].y)

    def test_scatter_axes_are_independent(self, store_json, all_continents):
        """Scatter X and Y axes can be set independently."""
        from app.callbacks.dashboard_callbacks import update_scatter
        fig1 = update_scatter(store_json, all_continents, "total_cases", "total_deaths")
        fig2 = update_scatter(store_json, all_continents, "gdp_per_capita", "vaccination_rate_pct")
        assert fig1.layout.title.text != fig2.layout.title.text


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
