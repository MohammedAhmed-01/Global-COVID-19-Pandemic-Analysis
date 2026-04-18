```
COVID19-Pandemic-Dashboard/
│
├── data/
│   ├── raw/
│   │   └── owid-covid-data.csv
│   ├── processed/
│   │   └── covid_cleaned.csv
│
├── notebooks/
│   ├── 01_data_cleaning.ipynb
│   ├── 02_eda_analysis.ipynb
│   └── 03_metric_preparation.ipynb
│
├── app/
│   ├── components/
│   │   ├── filters.py
│   │   ├── comparison_charts.py
│   │   ├── relationship_charts.py
│   │   ├── distribution_charts.py
│   │   └── time_series_charts.py
│   │
│   ├── layout/
│   │   └── dashboard_layout.py
│   │
│   ├── callbacks/
│   │   └── dashboard_callbacks.py
│
├── assets/
│   └── style.css
│
├── utils/
│   ├── data_loader.py
│   └── helper_functions.py
│
├── app.py
├── requirements.txt
└── README.md
```