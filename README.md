# Brazil Port Data

Source of [brazilportdata.com](https://www.brazilportdata.com): a research hub on the Brazilian port sector built on official ANTAQ statistics, extended with a European maritime observatory (EU MRV, Eurostat, Sentinel-5P).

## What is in this repository

| Path | Content |
|---|---|
| `index.html` | The home page: eleven project cards, the *Brazil at a Glance* strip and the About and Contact sections. Static HTML, no build step. |
| `CNAME`, `favicon.svg`, `og-image.png` | Domain and site assets. |

The dashboards linked from the home page live in their own repositories and Vercel projects (PortFlow Brasil, Ports & Terminals Explorer, Brazilian Berthings, Brazil Port Call Monitor, OPS Priority Atlas, SDG Port Hub, European Maritime Observatory and others).

## Data

All Brazilian figures come from ANTAQ's *Estatístico Aquaviário* (open data, ODbL), aggregated with the same definition ANTAQ uses for port movement (authorised cargo operations). Coverage runs from 2010 to February 2026; 2026 rows are partial.

The consolidated annual tables are published separately on Zenodo: *Brazil Port Data: consolidated ANTAQ port statistics, 2010-2026*, [doi:10.5281/zenodo.23158267](https://doi.org/10.5281/zenodo.23158267).

## Updating

ANTAQ publishes monthly. The home page numbers are refreshed from the ANTAQ panel; the extraction date is shown on the page.

## Licence

Code: MIT. Data: derived from ANTAQ open data under the Open Data Commons Open Database License (ODbL); please credit ANTAQ and Brazil Port Data.

## Author

Darliane Cunha, PhD, Federal University of Maranhão (UFMA). darliane@brazilportdata.com
