[brazil-port-data_README.md](https://github.com/user-attachments/files/28936645/brazil-port-data_README.md)
# brazil-port-data

> Documented ETL pipeline and open data product for Brazilian port cargo movement, built from ANTAQ statistics (2010-2024).

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org)

## Overview

`brazil-port-data` consolidates raw ANTAQ port statistics into a clean, analysis-ready dataset and powers the dashboards at [brazilportdata.com](https://brazilportdata.com). It documents the full path from raw public data to interactive visualisation.

## Features

- Reproducible ETL from ANTAQ open data (2010-2024)
- Cleaning, harmonisation and validation steps
- Cargo flow, port and terminal aggregations
- Ready-to-use CSV/Parquet outputs
- Example dashboards (Plotly / Streamlit)

## Quick start

```bash
python -m brazil_port_data.etl --years 2010-2024 --out data/clean/
```

```python
import pandas as pd
df = pd.read_parquet("data/clean/cargo_movements.parquet")
df.groupby("port")["tonnes"].sum().sort_values(ascending=False).head()
```

## Repository structure

```
brazil-port-data/
├── brazil_port_data/    # ETL pipeline
├── data/raw/            # source extracts (or download script)
├── data/clean/          # processed outputs
├── dashboards/          # Plotly / Streamlit apps
└── docs/                # data dictionary + sources
```

## Data source

ANTAQ (National Waterway Transport Agency) open statistics.

