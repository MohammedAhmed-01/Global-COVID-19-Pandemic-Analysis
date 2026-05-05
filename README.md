# 🦠 Global COVID-19 Pandemic Analysis — ViraLens

![Power BI Dashboard Home](PowerBiDashBoard/Home.png)

---

## 📌 Overview

This project presents an end-to-end data analysis pipeline for understanding the global impact of the COVID-19 pandemic using real-world data from **Our World in Data**.

The main goal is not only to visualize the data, but to:

- Understand the data behavior
- Handle real-world data challenges
- Generate reliable insights
- Build interactive dashboards

---

## 🎯 Objectives

- Analyze global COVID-19 trends across countries
- Handle missing and inconsistent data effectively
- Perform robust feature engineering
- Build interactive dashboards (Power BI & Streamlit)
- Deliver meaningful and non-misleading insights

---

## 📊 Dataset

| Property    | Details               |
|-------------|----------------------|
| **Source**  | [Our World in Data](https://ourworldindata.org/covid-deaths) |
| **Rows**    | 395,312              |
| **Columns** | 80+                  |
| **Type**    | Time Series          |
| **Granularity** | Daily per country |

---

## 🏗️ Project Architecture

```
Raw Data → Data Cleaning → Feature Engineering → Analysis → Visualization
```

---

## 📁 Project Structure

```
GLOBAL-COVID-19-PANDEMIC-ANALYSIS/
│
├── .qodo/                     # Environment / config files
├── Atthacment/                # Supporting assets / files
│
├── Data/
│   ├── Raw/                   # Original dataset (immutable)
│   └── Processed/             # Cleaned & transformed data
│
├── Documents/                 # Project documentation
├── Notebooks/                 # Jupyter notebooks (EDA & analysis)
│
├── outputs/                   # Generated outputs & results
│
├── PowerBiDashBoard/          # Power BI dashboard (.pbix)
├── StreamlitDashBoard/        # Streamlit app (interactive dashboard)
│
├── .gitattributes
└── README.md
```

---

## 🧠 Key Challenge — Missing Values

Handling missing values was the most critical part of this project.

### 🔍 Observations

- Missing values were **not random**
- Some countries didn't report certain metrics (e.g., testing)
- Some columns had **irregular updates**
- Missing data sometimes **carried meaning**

> ⚠️ **Important Insight:**
> **Missing ≠ Error** — Sometimes, missing values represent real-world limitations.

### ⚙️ Data Cleaning Strategy

Instead of applying a single rule, a **column-wise strategy** was used:

- ✔️ Context-based decisions
- ✔️ Country-level awareness
- ✔️ Time-series consistency

**Techniques Used:**

| Technique | When Applied |
|-----------|-------------|
| Forward Fill | Metrics that carry over (e.g., total cases) |
| Interpolation | Gradual changes between known values |
| Keeping NaN | When data was genuinely unavailable |
| Ignoring columns | Unreliable or sparsely populated features |

---

## 🔬 Feature Engineering

To improve analysis quality and fairness across countries:

### 📈 Normalization
- `cases_per_million`
- `deaths_per_million`

### 🧮 Ratios
- `case_fatality_rate`
- `testing_rate`
- `vaccination_rate_pct`

### ⏳ Time-Series Smoothing
- `cases_7day_ma`
- `deaths_7day_ma`

> 👉 This helped reduce noise and reveal real trends.

---

## 📊 Dashboards

### 🟣 Power BI Dashboard

Located in: `PowerBiDashBoard/`

**Features:**
- Country & continent slicers
- KPI indicators
- Trend analysis
- Comparative visuals

### 🟢 Streamlit Dashboard

Located in: `StreamlitDashBoard/`

**Features:**
- Interactive filters
- Dynamic charts
- Real-time exploration

---

## 📈 Key Insights

- **High testing → higher reported cases** (not necessarily worse conditions)
- **Raw numbers are misleading** without normalization
- **Vaccination reduced severity** more than spread
- **Data inconsistency** affects global comparisons

---

## ⚠️ Common Pitfalls Avoided

| ❌ Pitfall | ✅ Approach Taken |
|-----------|-----------------|
| Blindly filling missing values | Used context-aware strategies |
| Creating artificial data | Kept NaN when appropriate |
| Ignoring data context | Applied country-level awareness |
| Misleading visualizations | Normalized metrics before comparing |

---

## 🚀 Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Data processing |
| Pandas | Data manipulation |
| NumPy | Numerical operations |
| Jupyter Notebook | Analysis & EDA |
| Power BI | Interactive dashboard |
| Streamlit | Web dashboard |

---



## 📬 Contact

Feel free to connect or reach out for discussion or feedback.

---

## ⭐ Support

If you found this project useful, consider giving it a **⭐ on GitHub**!
