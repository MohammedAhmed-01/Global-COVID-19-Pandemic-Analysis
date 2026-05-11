# 🦠 COVID-19 Global Pandemic Analysis Dashboard

## Project Overview

A fully interactive **Plotly Dash** dashboard that analyses the global spread, impact, and recovery patterns of the COVID-19 pandemic.
The dashboard enables users to compare pandemic metrics across countries and continents, explore relationships between socio-economic factors and outcomes, examine key health metric distributions, and track pandemic progression over time.

---

## Dataset Description

| Property | Value |
|----------|-------|
| **Name** | Our World in Data — COVID-19 Dataset |
| **Source** | <https://github.com/owid/covid-19-data/tree/master/public/data> |
| **File** | `owid-covid-data.csv` (or cleaned version `owid_covid_cleaned.csv`) |
| **Size** | ~200,000+ rows · 67 columns |
| **Coverage** | Daily country-level data from January 2020 |

Key columns used:
- `location`, `continent`, `date`
- `total_cases`, `total_deaths`, `new_cases`, `new_deaths`
- `total_vaccinations`, `people_fully_vaccinated_per_hundred`
- `gdp_per_capita`, `population`, `population_density`
- `new_cases_smoothed`, `new_deaths_smoothed` (7-day MA)

---

## Objectives

1. **Pandemic Progression** — Visualise the global timeline of cases and deaths via Line and Area charts
2. **Global Impact** — Compare total burden across countries and continents
3. **Vaccination Insights** — Explore vaccination coverage and its relationship with outcomes
4. **Country Comparisons** — Enable side-by-side analysis of any two metrics via interactive Scatter and Bubble charts

---

## Chart Coverage (All 9 Weeks)

| Week | Category | Chart Type |
|------|----------|-----------|
| 1 | Comparison | Column Chart **+** Bar Chart |
| 2 | Comparison | Stacked Column · Stacked Bar · Clustered Column · Clustered Bar |
| 3 | Relationship | Scatter Chart |
| 4 | Relationship | Bubble Chart |
| 5 | Distribution | Histogram |
| 6 | Distribution | Box Chart |
| 7 | Distribution | Violin Chart |
| 8 | Time-Series | Line Chart |
| 9 | Time-Series | Area Chart |

---

## Interactive Elements (≥ 3 required)

| # | Control | ID | Effect |
|---|---------|-----|--------|
| 1 | **Continent Dropdown** (multi-select) | `dd-continent` | Filters all charts by continent |
| 2 | **Metric Dropdown** | `dd-metric` | Changes the primary metric displayed across Overview / Distribution charts |
| 3 | **Top-N Slider** | `slider-topn` | Sets how many countries appear in Column/Bar charts |
| 4 | **View Radio** | `radio-view` | Toggles Absolute / Per-Million / Percent normalisation |
| 5 | **Scatter X/Y Dropdowns** | `dd-scatter-x/y` | Independently choose axes of the Scatter chart |
| 6 | **Table Search** | `table-search` | Live filter on the data table |
| 7 | **Export Button** | `btn-export` | Downloads the filtered dataset as CSV |

---

## Tools & Technologies

- **Python 3.11+**
- **Dash 2.17+** by Plotly — dashboard framework
- **Plotly 5.22+** — all chart types (Express + Graph Objects)
- **Dash Bootstrap Components 1.5+** — responsive layout
- **Pandas 2.1+** — data loading & preprocessing
- **NumPy 1.26+** — numerical utilities

---

## Project Structure

```
Team_COVID19Analysis/
├── app.py                              # Main entry point
├── requirements.txt                    # Python dependencies
├── README.md                           # This file
├── data/
│   └── owid_covid_cleaned.csv          # Cleaned dataset (place here)
└── app/
    ├── __init__.py
    ├── layout/
    │   ├── __init__.py
    │   └── dashboard_layout.py         # Full Dash UI layout
    └── callbacks/
        ├── __init__.py
        └── dashboard_callbacks.py      # All 12 Dash callbacks
```

---

## Setup & Run Instructions

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Place your dataset
Copy your CSV file to `./data/owid_covid_cleaned.csv`
(Or use any path — you can enter it in the dashboard's loader input.)

### 3. Run the dashboard
```bash
python app.py
```

### 4. Open in browser
```
http://127.0.0.1:8050/
```

---

## Dashboard Sections

| Section | Charts |
|---------|--------|
| **Overview** | Column Chart, Bar Chart (Week 1) |
| **Comparisons** | Stacked Column/Bar, Clustered Column/Bar (Week 2) |
| **Relationships** | Scatter Chart (Week 3), Bubble Chart (Week 4) |
| **Distributions** | Histogram (Week 5), Box (Week 6), Violin (Week 7) |
| **Trends** | Line Chart (Week 8), Area Chart (Week 9) |
| **Data Table** | Searchable + exportable country table |

---

## Data Storytelling

### 🔴 Pandemic Progression
The Line and Area charts in the **Trends** section reveal the successive COVID-19 waves — from the initial 2020 outbreak, through the Alpha/Delta surges of 2021, to the massive Omicron peak in early 2022 — and the gradual subsidence thereafter.

### 🌍 Global Impact
The Column and Bar charts under **Overview** show the stark disparity between nations. The United States, India, and France registered the highest absolute case counts, while smaller island nations record near-zero figures. Switching to *per-million* normalisation reframes the story: densely vaccinated European nations often show higher detected case rates relative to their population.

### 💉 Vaccination Insights
The Bubble Chart (GDP vs Cases/Million) reveals a nuanced relationship: wealthier nations generally achieved higher vaccination coverage yet still experienced significant Omicron waves due to the variant's immune-evasive properties. The Scatter chart of vaccination rate vs CFR shows a moderate negative correlation — higher vaccination is associated with lower case-fatality rates.

### 🌐 Country Comparisons
The Stacked/Clustered charts aggregate totals by continent. Asia and Europe dominate absolute case and death counts, while Africa — despite lower testing rates — shows proportionally lower deaths, partly attributable to demographic age structure (visible in the Violin chart comparing median age distributions).

---

## Member Roles

| Member | Responsibility |
|--------|---------------|
| Member 1 | Data collection & raw dataset sourcing |
| Member 2 | Data preprocessing notebook (Jupyter) |
| Member 3 | Chart implementation — Weeks 1–4 |
| Member 4 | Chart implementation — Weeks 5–9 |
| **Member 5** | **Dashboard layout, callbacks, documentation & data storytelling** |
