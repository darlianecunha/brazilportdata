# Brazil Port Data

Source of [brazilportdata.com](https://www.brazilportdata.com): a research hub on the Brazilian port sector built on official ANTAQ statistics, extended with a European maritime observatory (EU MRV, Eurostat, Sentinel-5P).

## What is in this repository

| Path | Content |
|---|---|
| `index.html` | The home page: twelve project cards, the *Brazil at a Glance* strip and the About and Contact sections. Static HTML, no build step. |
| `data/` | Consolidated ANTAQ datasets (CSV and JSON) that feed the cards and dashboards, with a data dictionary in `data/README.md`. |
| `CNAME`, `favicon.svg`, `og-image.png` | Domain and site assets. |

The dashboards linked from the home page live in their own repositories and Vercel projects (PortFlow Brasil, Ports & Terminals Explorer, Brazilian Berthings, Brazil Port Call Monitor, SDG Port Hub, European Maritime Observatory and others).

## Data

All Brazilian figures come from ANTAQ's *Estatístico Aquaviário* (open data, ODbL), extracted from the agency's statistical panel and aggregated with the same definition ANTAQ uses for port movement (authorised cargo operations). Coverage runs from 2010 to February 2026; 2026 rows are partial. See `data/README.md` for file layouts, definitions and the extraction dates.

```python
import pandas as pd
df = pd.read_csv("data/cargo_by_installation_2010_2026.csv")
df[df.ano == 2025].groupby("complexo")["toneladas"].sum().sort_values(ascending=False).head()
```

## Updating

ANTAQ publishes monthly. The home page numbers and the `data/` files are refreshed from the ANTAQ panel; the extraction date is shown on the page and in the data dictionary.

## Licence

Code: MIT. Data: derived from ANTAQ open data under the Open Data Commons Open Database License (ODbL); please credit ANTAQ and Brazil Port Data.

## Author

Darliane Cunha, PhD, Federal University of Maranhão (UFMA). darliane@brazilportdata.com
